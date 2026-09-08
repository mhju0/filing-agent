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

from memory_monitor import Monitor
from pilot import AUDIT, calculated, load_catalog, unload
from run import ROOT, api, local_model_info, select_models, timed_chat
from scoring import reject_constant, unique_object

SCHEMA = {'type': 'object', 'properties': {
    'companies': {'type': 'array', 'items': {'type': 'string', 'enum': ['Samsung', 'NAVER', 'Microsoft']}},
    'metric': {'type': ['string', 'null'], 'enum': ['revenue', 'operating_income', 'net_income', 'research_and_development', None]},
    'periods': {'type': 'array', 'items': {'type': 'string', 'pattern': '^[0-9]{4}$'}},
    'basis': {'type': 'string', 'enum': ['consolidated', 'separate']},
    'action': {'type': 'string', 'enum': ['report', 'compare']}},
    'required': ['companies', 'metric', 'periods', 'basis', 'action'], 'additionalProperties': False}
OPTIONS = {'temperature': 0, 'seed': 42, 'num_ctx': 4096, 'num_predict': 256}
COPY = {
    'outside_verified_metric_scope': ('현재 검증된 근거 범위에는 요청한 지표가 없습니다. 공시 전체에 없다는 뜻은 아닙니다.', 'The requested metric is outside the verified evidence scope; this does not mean it is absent from the entire filing.'),
    'missing_period': ('요청한 회사와 연도에 해당하는 검증된 수치가 없습니다.', 'No verified figure is available for the requested company and fiscal year.'),
    'unsupported_basis': ('현재 검증된 근거는 연결 기준입니다. 별도 기준 수치는 제공할 수 없습니다.', 'The verified evidence is consolidated; separate-statement figures are unavailable.'),
    'incompatible_currency': ('통화가 달라 증감률을 계산할 수 없습니다.', 'A percentage change cannot be calculated across different currencies.'),
    'incompatible_comparison': ('현재 근거로는 요청한 증감률을 계산할 수 없습니다.', 'The requested percentage change is not supported by comparable evidence.'),
    'ambiguous_context': ('회사, 지표 또는 회계연도를 지정해 주세요.', 'Please specify the company, metric, or fiscal year.'),
}


def parse_intent(content):
    intent = json.loads(content, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(intent, dict) or set(intent) != set(SCHEMA['required']):
        raise ValueError('Invalid intent keys')
    for key in ('companies', 'periods'):
        if not isinstance(intent[key], list) or not all(isinstance(x, str) for x in intent[key]) or len(set(intent[key])) != len(intent[key]):
            raise ValueError('Invalid intent list')
    if any(c not in ('Samsung', 'NAVER', 'Microsoft') for c in intent['companies']):
        raise ValueError('Unknown company')
    if any(not re.fullmatch(r'[0-9]{4}', p) for p in intent['periods']):
        raise ValueError('Invalid fiscal year')
    if intent['metric'] not in SCHEMA['properties']['metric']['enum'] or intent['basis'] not in ('consolidated', 'separate') or intent['action'] not in ('report', 'compare'):
        raise ValueError('Invalid intent enum')
    return intent


def resolve(intent, catalog):
    result = {'companies': intent['companies'], 'metric': intent['metric'], 'periods': intent['periods'],
              'operation': intent['action'], 'fact_ids': [], 'refused': False, 'reason_code': None,
              'figures': [], 'calculated': [], 'answer_ko': '', 'answer_en': ''}
    def blocked(reason):
        result.update(operation='clarify' if reason == 'ambiguous_context' else 'refuse',
                      refused=reason != 'ambiguous_context', reason_code=reason)
        result['answer_ko'], result['answer_en'] = COPY[reason]
        return result
    if not intent['companies'] or not intent['periods'] or intent['metric'] is None:
        return blocked('ambiguous_context')
    if intent['basis'] != 'consolidated':
        return blocked('unsupported_basis')
    if intent['metric'] not in {f['metric'] for f in catalog}:
        return blocked('outside_verified_metric_scope')
    selected = [f for f in catalog if f['company'] in intent['companies'] and f['period'] in intent['periods'] and f['metric'] == intent['metric'] and f['basis'] in ('consolidated', 'consolidated_entity_total')]
    if len(selected) != len(intent['companies']) * len(intent['periods']):
        return blocked('missing_period')
    if intent['action'] == 'compare':
        if len({f['currency'] for f in selected}) != 1:
            return blocked('incompatible_currency')
        try:
            change = calculated(selected)
        except ValueError:
            return blocked('incompatible_comparison')
        result['calculated'] = [change]
        # Sign and both languages come from the same checked arithmetic result.
        sign = Decimal(change['absolute_change'])
        ko, en = ('감소했습니다', 'decreased') if sign < 0 else (('증가했습니다', 'increased') if sign > 0 else ('동일합니다', 'was unchanged'))
        company = intent['companies'][0]
        company_ko = {'Samsung': '삼성전자', 'NAVER': '네이버', 'Microsoft': '마이크로소프트'}[company]
        metric_ko, metric_en = {'revenue': ('매출액', 'revenue'), 'operating_income': ('영업이익', 'operating income'), 'net_income': ('당기순이익', 'net income')}[intent['metric']]
        prior, current = sorted(intent['periods'])
        result['answer_ko'] = f'{company_ko}의 {current}년 {metric_ko}은 {prior}년보다 {ko}.' if sign else f'{company_ko}의 {current}년 {metric_ko}은 {prior}년과 {ko}.'
        result['answer_en'] = f"{company}'s {metric_en} {en} in FY{current} compared with FY{prior}."
    else:
        result['answer_ko'] = '요청한 회사, 지표, 회계연도의 검증된 수치입니다.'
        result['answer_en'] = 'These are the verified figures for the requested company, metric and fiscal year.'
    result['figures'] = selected
    result['fact_ids'] = [f['id'] for f in selected]
    return result


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
                            answer = resolve(intent, catalog)
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
