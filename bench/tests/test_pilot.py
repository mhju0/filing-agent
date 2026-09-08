import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pilot


class PilotTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.catalog = pilot.load_catalog()
        self.cases = json.loads((pilot.ROOT / 'pilot-cases.json').read_text())

    def answer(self, turn):
        return {**copy.deepcopy(turn['expected']), 'answer_ko': '검증된 근거 범위를 확인했습니다.',
                'answer_en': 'The verified evidence scope is shown.'}

    def test_all_case_oracles_and_source_ids_resolve(self):
        for case in self.cases:
            for turn in case['turns']:
                result = pilot.assess(json.dumps(self.answer(turn)), turn['expected'], self.catalog)
                self.assertTrue(result['accuracy'], case['id'])

    def test_comparison_exact_independent_value(self):
        turn = self.cases[0]['turns'][0]
        result = pilot.assess(json.dumps(self.answer(turn)), turn['expected'], self.catalog)
        self.assertEqual(result['calculated_by_code']['absolute_change'], '-43295866000000')
        self.assertEqual(result['calculated_by_code']['percentage_change'], '-14.33')

    def test_changed_evidence_snapshot_rejected(self):
        corrupted = copy.deepcopy(self.snapshot)
        corrupted['facts'][0]['value'] = '1'
        with self.assertRaises(ValueError):
            pilot.verify_snapshot(corrupted)

    def test_wrong_company_source_and_extra_id_fail(self):
        turn = self.cases[1]['turns'][1]
        for ids in [['untrusted:source'], self.cases[1]['turns'][0]['expected']['fact_ids'],
                    turn['expected']['fact_ids'] * 2]:
            answer = self.answer(turn)
            answer['fact_ids'] = ids
            self.assertFalse(pilot.assess(json.dumps(answer), turn['expected'], self.catalog)['accuracy'])

    def test_missing_zero_and_borrowed_fact_disqualify(self):
        turn = self.cases[2]['turns'][0]
        answer = self.answer(turn)
        answer['answer_en'] = 'The expense was 0.'
        self.assertTrue(pilot.assess(json.dumps(answer), turn['expected'], self.catalog)['refusal_violation'])
        answer = self.answer(turn)
        answer['fact_ids'] = [self.catalog[0]['id']]
        self.assertTrue(pilot.assess(json.dumps(answer), turn['expected'], self.catalog)['refusal_violation'])

    def test_arithmetic_rejects_currency_basis_period_and_zero(self):
        ids = self.cases[0]['turns'][0]['expected']['fact_ids']
        selected = [copy.deepcopy(f) for f in self.catalog if f['id'] in ids]
        for key, value in [('currency', 'USD'), ('basis', 'separate'), ('period_end', '2023-09-30'), ('value', '0')]:
            facts = copy.deepcopy(selected)
            facts[0][key] = value
            with self.assertRaises(ValueError):
                pilot.calculated(facts)

    def test_duplicate_keys_and_schema_violation_fail(self):
        turn = self.cases[0]['turns'][0]
        answer = self.answer(turn)
        answer['value'] = '123456'
        self.assertFalse(pilot.assess(json.dumps(answer), turn['expected'], self.catalog)['accuracy'])
        self.assertFalse(pilot.assess('{"refused":true,"refused":false}', turn['expected'], self.catalog)['parse'])


if __name__ == '__main__':
    unittest.main()
