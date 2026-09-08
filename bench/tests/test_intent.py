import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import intent


class IntentTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.catalog = intent.load_catalog()
        self.cases = json.loads((intent.ROOT / 'pilot-cases.json').read_text())

    def test_policy_matches_all_cases_without_receiving_oracle(self):
        for case in self.cases:
            for turn in case['turns']:
                expected = turn['expected']
                query = {k: expected[k] for k in ('companies', 'metric', 'periods')}
                query['basis'] = 'separate' if case['id'] == 'unsupported_basis' else 'consolidated'
                query['action'] = 'compare' if case['id'] in ('compare_ko', 'compare_us_en', 'incompatible_currency') else 'report'
                answer = intent.resolve(intent.parse_intent(json.dumps(query)), self.catalog)
                self.assertTrue(intent.matches(answer, expected), case['id'])
                if expected['refused']:
                    self.assertEqual(answer['figures'], [])
                    self.assertEqual(answer['calculated'], [])

    def test_wrong_company_is_not_silently_substituted(self):
        query = {'companies': ['NAVER'], 'metric': 'revenue', 'periods': ['2022'], 'basis': 'consolidated', 'action': 'report'}
        answer = intent.resolve(query, self.catalog)
        self.assertEqual(answer['reason_code'], 'missing_period')
        self.assertEqual(answer['fact_ids'], [])

    def test_samsung_comparison_direction_in_both_languages(self):
        query = {'companies': ['Samsung'], 'metric': 'revenue', 'periods': ['2023', '2022'], 'basis': 'consolidated', 'action': 'compare'}
        answer = intent.resolve(query, self.catalog)
        self.assertIn('감소했습니다', answer['answer_ko'])
        self.assertIn('decreased', answer['answer_en'])
        self.assertEqual(answer['calculated'][0]['percentage_change'], '-14.33')

    def test_nonzero_change_rounding_to_zero_is_not_flat(self):
        catalog = copy.deepcopy(self.catalog)
        selected = [f for f in catalog if f['company'] == 'Samsung' and f['metric'] == 'revenue']
        for f in selected:
            f['value'] = '100000001' if f['period'] == '2023' else '100000000'
        query = {'companies': ['Samsung'], 'metric': 'revenue', 'periods': ['2023', '2022'], 'basis': 'consolidated', 'action': 'compare'}
        answer = intent.resolve(query, catalog)
        self.assertEqual(answer['calculated'][0]['percentage_change'], '0.00')
        self.assertIn('increased', answer['answer_en'])

    def test_duplicate_fields_unknown_keys_and_companies_rejected(self):
        base = {'companies': ['Samsung'], 'metric': 'revenue', 'periods': ['2023'], 'basis': 'consolidated', 'action': 'report'}
        for raw in [json.dumps({**base, 'value': '0'}), json.dumps({**base, 'companies': ['made-up']}),
                    json.dumps({**base, 'periods': ['2023', '2023']}), '{"metric":"revenue","metric":"net_income"}']:
            with self.assertRaises(ValueError):
                intent.parse_intent(raw)


if __name__ == '__main__':
    unittest.main()
