#!/usr/bin/env python3
"""Recheck the saved September 7 model evidence without inference or network calls."""

import hashlib
import json
from pathlib import Path

import intent
import pilot
from scoring import score

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / 'runs/2026-09-07'


def main():
    snapshot, catalog = pilot.load_catalog()
    count = calls = 0
    verified = {}
    original_cases = {c['id']: c for c in json.loads((BASE / 'cases.json').read_text())}
    pilot_cases = {c['id']: c for c in json.loads((BASE / 'pilot-cases.json').read_text())}
    for suite in ('original', 'pilot', 'intent'):
        result = json.loads((EVIDENCE / suite / 'results.json').read_text())
        assert result['status'] == 'complete'
        for name, digest in result['input_sha256'].items():
            path = (BASE if suite == 'original' else BASE.parent) / name
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, str(path)
        suite_count = suite_correct = 0
        for entry in result['results']:
            assert len(entry['runs']) == 3
            case = (original_cases if suite == 'original' else pilot_cases)[entry['case']]
            for trial in entry['runs']:
                assert len(trial['turns']) == len(case['turns'])
                checks = []
                for turn, expected_turn in zip(trial['turns'], case['turns']):
                    calls += 1
                    assert turn['question'] == expected_turn['question']
                    if suite == 'original':
                        fixture = json.loads((BASE / 'fixtures' / expected_turn['fixture']).read_text())
                        checked = score(turn['content'], fixture, expected_turn['expected'], turn['question'])
                        assert checked == turn['score']
                        checks.append(checked['accuracy'])
                    elif suite == 'pilot':
                        checked = pilot.assess(turn['content'], expected_turn['expected'], catalog)
                        assert checked == turn['score']
                        checks.append(checked['accuracy'])
                    else:
                        checked = intent.resolve(intent.parse_intent(turn['content']), catalog)
                        bound = {f['id']: f['source'] for f in snapshot['facts'] if f['id'] in checked['fact_ids']}
                        checked['source_bindings'] = bound
                        assert checked == turn['answer']
                        checks.append(intent.matches(checked, expected_turn['expected']))
                    assert turn['metrics']['done'] is True and turn['metrics']['done_reason'] != 'length'
                assert all(checks) == trial['accuracy']
                suite_correct += trial['accuracy']
                suite_count += 1
                count += 1
        verified[suite] = {'case_runs': suite_count, 'mechanical_passes': suite_correct,
                           'note': 'Pilot mechanical checks exclude prose semantics; see semantic-review.json.'}
    assert json.loads((BASE / 'results.json').read_text()) == json.loads((EVIDENCE / 'original/results.json').read_text())
    summary = {'status': 'PASS', 'case_runs_verified': count, 'actual_chat_responses_verified': calls,
               'source_snapshot_id': snapshot['snapshot_id'], 'suites': verified,
               'scope': 'Offline artifact integrity, scores and source bindings; not a new inference run or complete application certification.'}
    (EVIDENCE / 'verification.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
