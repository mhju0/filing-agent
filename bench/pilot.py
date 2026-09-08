#!/usr/bin/env python3
"""Bounded evidence-selection experiment, not a production router or replay."""

import hashlib
import json
import os
import statistics
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from slice.financial import verify_snapshot, calculated

from memory_monitor import Monitor, command
from run import ROOT, api, local_model_info, select_models, timed_chat
from scoring import number_tokens, reject_constant, unique_object

AUDIT = ROOT.parent / 'docs/audits/2026-09-07-coverage'
OPTIONS = {'temperature': 0, 'seed': 42, 'num_ctx': 8192, 'num_predict': 768}
KEYS = {'companies', 'metric', 'periods', 'operation', 'fact_ids', 'refused', 'reason_code', 'answer_ko', 'answer_en'}


def load_catalog():
    snapshot = json.loads((AUDIT / 'pilot-snapshot.json').read_text())
    verify_snapshot(snapshot)
    return snapshot, [{**{key: fact[key] for key in ('id', 'metric', 'period', 'period_start', 'period_end', 'basis', 'value', 'currency', 'source_label')},
                       'company': 'Samsung' if fact['company'] == '삼성전자' else fact['company']}
                      for fact in snapshot['facts']]






def assess(content, expected, catalog):
    result = {'parse': False, 'accuracy': False, 'prohibited_numeric_tokens': [], 'refusal_violation': False}
    try:
        output = json.loads(content, parse_constant=reject_constant, object_pairs_hook=unique_object)
        result['parse'] = True
    except (ValueError, TypeError):
        output = content
    allowed_years = {fact['period'] for fact in catalog} | set(expected['periods'])
    if not isinstance(output, dict):
        result['prohibited_numeric_tokens'] = [n for n in number_tokens(content) if n not in allowed_years]
        result['refusal_violation'] = bool(expected['refused'] and result['prohibited_numeric_tokens'])
        return result
    prose = [output.get(k, '') for k in ('answer_ko', 'answer_en')]
    result['prohibited_numeric_tokens'] = [n for n in number_tokens(prose) if n not in allowed_years]
    result['refusal_violation'] = bool(expected['refused'] and
                                      (output.get('fact_ids') or result['prohibited_numeric_tokens']))
    if set(output) != KEYS or type(output.get('refused')) is not bool:
        return result
    if not all(isinstance(output[k], str) and output[k].strip() for k in ('answer_ko', 'answer_en')):
        return result
    for key, value in expected.items():
        actual = output.get(key)
        if isinstance(value, list):
            if not isinstance(actual, list) or any(not isinstance(x, str) for x in actual) or sorted(actual) != sorted(value):
                return result
        elif actual != value:
            return result
    if result['prohibited_numeric_tokens']:
        return result
    by_id = {f['id']: f for f in catalog}
    selected = [by_id[key] for key in output['fact_ids']]
    result['resolved_figures'] = selected
    if output['operation'] == 'compare':
        try:
            result['calculated_by_code'] = calculated(selected)
        except ValueError as exc:
            result['error'] = str(exc)
            return result
    result['accuracy'] = True
    return result


def unload(model):
    api('POST', '/api/generate', {'model': model, 'keep_alive': 0}, timeout=15)
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if not api('GET', '/api/ps').get('models'):
            return
        time.sleep(.2)
    raise RuntimeError('Model unload not confirmed; refusing further generation')


def report(result):
    lines = ['# Verified-pilot local model experiment', '', 'Status: ' + result['status'], '',
             '| Model | Case | Load-inclusive seconds (n=1) | Warm median seconds (n=2) | Accuracy | Parse | Refusal violations |',
             '| --- | --- | ---: | ---: | --- | --- | ---: |']
    for row in result['results']:
        trials = row['runs']
        cold = f"{trials[0]['wall_seconds']:.2f}" if trials else 'N/A'
        warm = f"{statistics.median(t['wall_seconds'] for t in trials[1:]):.2f}" if len(trials) > 1 else 'N/A'
        lines.append(f"| {row['model']} | {row['case']} | {cold} | {warm} | {sum(t['accuracy'] for t in trials)}/3 | {sum(t['parse'] for t in trials)}/3 | {sum(t['refusal_violation'] for t in trials)} |")
    lines += ['', 'Cold means explicitly unloaded, not a cleared OS file cache. Warm trials retain the model; switch time totals both turns.',
              'All cases receive the same complete 15-fact catalog, not a harness-selected company table. Source IDs resolve to pinned regulator evidence in code.',
              'Exact intent and evidence selection are scored against case expectations. Code computes changes; this experiment does not certify free-form financial prose or live retrieval.',
              'A financial amount is forbidden in model prose here. The numeric scanner misses spelled-out quantities; bilingual sentences require manual review.',
              'A refusal with selected facts or financial digits disqualifies that candidate configuration. Three deterministic repetitions are not independent statistical evidence.', '']
    return '\n'.join(lines)


def main():
    snapshot, catalog = load_catalog()
    cases = json.loads((ROOT / 'pilot-cases.json').read_text())
    system = (ROOT / 'prompts/pilot.txt').read_text()
    destination = Path(os.environ.get('PILOT_OUTPUT_DIR', str(ROOT / 'pilot-results'))).resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError('Output must stay within bench')
    destination.mkdir(parents=True, exist_ok=True)
    def save():
        for name, content in [('results.json', json.dumps(result, ensure_ascii=False, indent=2) + '\n'), ('results.md', report(result))]:
            temporary = destination / (name + '.tmp')
            temporary.write_text(content)
            temporary.replace(destination / name)
    installed = {m['name']: m for m in api('GET', '/api/tags')['models']}
    result = {'created_at': datetime.now(timezone.utc).isoformat(), 'status': 'running',
              'snapshot_id': snapshot['snapshot_id'], 'options': OPTIONS, 'keep_alive': '5m',
              'machine': {'chip': command('sysctl', '-n', 'machdep.cpu.brand_string'),
                          'ram_bytes': int(command('sysctl', '-n', 'hw.memsize')), 'macos': command('sw_vers', '-productVersion')},
              'runtime_version': api('GET', '/api/version'), 'models': {}, 'results': [],
              'input_sha256': {str(p.relative_to(ROOT.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [AUDIT / 'pilot-snapshot.json', ROOT / 'pilot-cases.json', ROOT / 'prompts/pilot.txt', ROOT / 'pilot.py']}}
    for model in select_models(installed):
        if model not in installed:
            result.setdefault('unrun', []).append({'model': model, 'reason': 'Not installed'})
            continue
        info = local_model_info(model)
        result['models'][model] = {'installed': installed[model], 'info': info}
        for case in cases:
            unload(model)
            entry = {'model': model, 'case': case['id'], 'runs': []}
            result['results'].append(entry)
            for repetition in range(3):
                print(f"{model} / {case['id']} / {repetition+1}/3", flush=True)
                messages = [{'role': 'system', 'content': system + '\nCATALOG:\n' + json.dumps(catalog, ensure_ascii=False)}]
                trial = {'turns': [], 'cache_state': 'unloaded' if repetition == 0 else 'warm'}
                with Monitor() as monitor:
                    started = time.monotonic()
                    for turn in case['turns']:
                        messages.append({'role': 'user', 'content': turn['question']})
                        payload = {'model': model, 'messages': messages, 'format': 'json', 'stream': False, 'options': OPTIONS, 'keep_alive': '5m'}
                        if 'thinking' in (info.get('capabilities') or []):
                            payload['think'] = False
                        response = timed_chat(payload, max(.01, 120 - (time.monotonic() - started)))
                        record = {'question': turn['question'], 'wall_seconds': response['wall_seconds']}
                        if 'error' in response:
                            record.update(response)
                            trial['turns'].append(record)
                            break
                        body = response['response']
                        content = body.get('message', {}).get('content', '')
                        record.update(content=content, score=assess(content, turn['expected'], catalog))
                        record['metrics'] = {k: body.get(k) for k in ('load_duration', 'prompt_eval_count', 'prompt_eval_duration', 'eval_count', 'eval_duration', 'done', 'done_reason')}
                        if body.get('done') is not True or body.get('done_reason') == 'length':
                            record['score']['accuracy'] = False
                            record['error'] = 'Incomplete generation'
                        trial['turns'].append(record)
                        messages.append({'role': 'assistant', 'content': content})
                    trial['wall_seconds'] = time.monotonic() - started
                trial['memory'] = monitor.summary()
                complete = len(trial['turns']) == len(case['turns'])
                trial['accuracy'] = complete and all(t.get('score', {}).get('accuracy', False) for t in trial['turns'])
                trial['parse'] = complete and all(t.get('score', {}).get('parse', False) for t in trial['turns'])
                trial['refusal_violation'] = any(t.get('score', {}).get('refusal_violation', False) for t in trial['turns'])
                entry['runs'].append(trial)
                save()
                if any(t.get('timeout') for t in trial['turns']):
                    result['status'] = 'partial: deadline reached; generation halted'
                    save()
                    unload(model)
                    return 2
        unload(model)
    result['status'] = 'partial' if result.get('unrun') else 'complete'
    save()
    return 0


if __name__ == '__main__':
    sys.exit(main())
