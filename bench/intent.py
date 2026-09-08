#!/usr/bin/env python3
"""Intent-only local experiment with deterministic evidence policy and bilingual copy."""

import json
import os
import re
import statistics
import sys
import time
import hashlib
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slice.financial import SCHEMA, COPY, parse_intent, resolve, financial_answer

from memory_monitor import Monitor
from pilot import AUDIT, calculated, load_catalog, unload
from run import ROOT, api, local_model_info, select_models, timed_chat
from scoring import reject_constant, unique_object

OPTIONS = {'temperature': 0, 'seed': 42, 'num_ctx': 4096, 'num_predict': 256}






def matches(answer, expected):
    return all(sorted(answer[key]) == sorted(value) if isinstance(value, list) else answer[key] == value
               for key, value in expected.items())


def report(result):
    lines = ['# Intent-only local experiment', '', 'Status: ' + result['status'], '',
             '| Model | Case | Load-inclusive seconds (n=1) | Warm median seconds (n=2) | End-to-end case checks | Parse |',
             '| --- | --- | ---: | ---: | --- | --- |']
    for row in result['results']:
        runs = row['runs']
        cold = f"{runs[0]['wall_seconds']:.2f}" if runs else 'N/A'
        warm = f"{statistics.median(t['wall_seconds'] for t in runs[1:]):.2f}" if len(runs) > 1 else 'N/A'
        lines.append(f"| {row['model']} | {row['case']} | {cold} | {warm} | {sum(t['accuracy'] for t in runs)}/3 | {sum(t['parse'] for t in runs)}/3 |")
    lines += ['', 'Model output is intent only. Code selects source-bound facts, decides refusal, calculates changes, and supplies both financial answer sentences.',
              'Case checks compare the resulting company, metric, periods, selected IDs and refusal state against expectations. Runtime resolution never receives that oracle.',
              'Known closed-vocabulary cases, three deterministic repetitions, no held-out evaluation. This is not a complete app or a certification of arbitrary question understanding.',
              'Cold means model-unloaded, not cleared file cache. Warm switch time is the sum of both turns. See JSON for raw intents, actual context, answers, source bindings, timings and memory.', '']
    return '\n'.join(lines)


def main():
    snapshot, catalog = load_catalog()
    cases = json.loads((ROOT / 'pilot-cases.json').read_text())
    system = (ROOT / 'prompts/intent.txt').read_text() + '\nSCHEMA: ' + json.dumps(SCHEMA)
    installed = {m['name']: m for m in api('GET', '/api/tags')['models']}
    models = select_models(installed) if os.environ.get('MODELS') else ['gemma4:e4b']
    destination = ROOT / 'intent-results'
    if os.environ.get('INTENT_OUTPUT_DIR'):
        destination = Path(os.environ['INTENT_OUTPUT_DIR']).resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError('Output must stay inside bench')
    destination.mkdir(parents=True, exist_ok=True)
    result = {'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'running', 'snapshot_id': snapshot['snapshot_id'],
              'options': OPTIONS, 'format': SCHEMA, 'keep_alive': '5m', 'runtime': api('GET', '/api/version'), 'models': {}, 'results': [],
              'scope': 'Model interprets intent only; code selects evidence and owns all financial output and refusal policy. Not a release evaluation.',
              'input_sha256': {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest() for p in
                               [ROOT / 'intent.py', ROOT / 'prompts/intent.txt', ROOT / 'pilot-cases.json', AUDIT / 'pilot-snapshot.json']}}
    def save():
        p = destination / 'results.json.tmp'
        p.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        p.replace(destination / 'results.json')
        p = destination / 'results.md.tmp'
        p.write_text(report(result))
        p.replace(destination / 'results.md')
    for model in models:
        if model not in installed:
            raise ValueError('Exact model tag is not installed')
        if installed[model].get('size', 0) <= 0:
            raise ValueError('No local model weights reported')
        info = local_model_info(model)
        result['models'][model] = {'installed': installed[model], 'info': info}
        for case in cases:
            unload(model)
            entry = {'model': model, 'case': case['id'], 'runs': []}
            result['results'].append(entry)
            for repetition in range(3):
                print(f"intent / {model} / {case['id']} / {repetition+1}/3", flush=True)
                context = None
                trial = {'turns': [], 'cache_state': 'unloaded' if repetition == 0 else 'warm'}
                with Monitor() as monitor:
                    started = time.monotonic()
                    for turn in case['turns']:
                        payload = {'model': model, 'messages': [{'role': 'system', 'content': system},
                                   {'role': 'user', 'content': 'CONTEXT: ' + json.dumps(context, ensure_ascii=False) + '\nQUESTION: ' + turn['question']}],
                                   'format': SCHEMA, 'stream': False, 'options': OPTIONS, 'keep_alive': '5m'}
                        if 'thinking' in (info.get('capabilities') or []):
                            payload['think'] = False
                        response = timed_chat(payload, max(.01, 120 - (time.monotonic() - started)))
                        record = {'question': turn['question'], 'prior_context': context, 'wall_seconds': response['wall_seconds'], 'accuracy': False, 'parse': False}
                        if 'error' in response:
                            record.update(response)
                            trial['turns'].append(record)
                            break
                        body = response['response']
                        record['content'] = body.get('message', {}).get('content', '')
                        record['metrics'] = {k: body.get(k) for k in ('load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration', 'done', 'done_reason')}
                        try:
                            intent = parse_intent(record['content'])
                            record['parse'] = True
                            answer = financial_answer(intent, snapshot, turn['question'])
                            answer['source_bindings'] = {f['id']: f['source'] for f in snapshot['facts'] if f['id'] in answer['fact_ids']}
                            record['answer'] = answer
                            record['accuracy'] = matches(answer, turn['expected']) and body.get('done') is True and body.get('done_reason') != 'length'
                            # Runtime resolution, not the test oracle, determines accepted context.
                            if answer['operation'] in ('report', 'compare'):
                                context = intent
                        except (ValueError, KeyError, TypeError) as exc:
                            record['error'] = str(exc)
                        trial['turns'].append(record)
                    trial['wall_seconds'] = time.monotonic() - started
                trial['memory'] = monitor.summary()
                trial['accuracy'] = len(trial['turns']) == len(case['turns']) and all(t['accuracy'] for t in trial['turns'])
                trial['parse'] = len(trial['turns']) == len(case['turns']) and all(t['parse'] for t in trial['turns'])
                entry['runs'].append(trial)
                save()
                if any(t.get('timeout') for t in trial['turns']):
                    result['status'] = 'partial: timeout'
                    save()
                    unload(model)
                    return 2
        unload(model)
    result['status'] = 'complete'
    save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
