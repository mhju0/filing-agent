import json
import unittest
from slice.core import SNAPSHOT, guard_intent
from slice.financial import financial_answer

BASE = dict(companies=['Samsung'], metric='revenue', periods=['2023'], basis='consolidated', action='report')


class NaturalFollowupTests(unittest.TestCase):
    def test_natural_comparison_keeps_company_metric_and_anchor_year(self):
        for question in ['2022년과 비교하면 얼마나 증가하거나 감소했어?', '얼마나 줄었어?', '그럼 2022년과 비교해줘',
                         '전년 대비 얼마나 늘었나요?', 'How much did it decrease compared to 2022?',
                         'How much did it grow year over year?', 'How much has it changed?']:
            with self.subTest(question=question):
                intent = guard_intent(question, {**BASE, 'periods': ['2022']}, BASE)
                self.assertEqual(intent['companies'], ['Samsung'])
                self.assertEqual(intent['periods'], ['2022', '2023'])
                self.assertEqual(intent['action'], 'compare')
                answer = financial_answer(intent, json.loads(SNAPSHOT.read_text()), question)
                self.assertEqual(answer['operation'], 'compare')
                self.assertLess(float(answer['calculated'][0]['percentage_change']), 0)

    def test_explicit_year_pair_replaces_previous_year(self):
        intent = guard_intent('Compare 2021 and 2022 revenue', {**BASE, 'periods': ['2021', '2022'], 'action': 'compare'}, BASE)
        self.assertEqual(intent['periods'], ['2021', '2022'])

    def test_bounded_followup_fills_omitted_model_context(self):
        intent = guard_intent('얼마나 줄었어?', {**BASE, 'companies': [], 'metric': None, 'periods': []}, BASE)
        self.assertEqual(intent['companies'], ['Samsung'])
        self.assertEqual(intent['metric'], 'revenue')
        self.assertEqual(intent['periods'], ['2022', '2023'])

    def test_relative_year_is_relative_to_selected_fiscal_year(self):
        for question in ['전년에는?', '그 전년도는?', 'What about the previous year?']:
            with self.subTest(question=question):
                intent = guard_intent(question, BASE, BASE)
                self.assertEqual(intent['periods'], ['2022'])
                self.assertEqual(intent['action'], 'report')

    def test_unknown_company_never_inherits_context(self):
        for question in ['테슬라는 얼마나 줄었어?', 'How much did Tesla decrease?',
                         '2022년 테슬라와 비교하면?', 'Apple year over year?']:
            with self.subTest(question=question):
                self.assertEqual(guard_intent(question, {**BASE, 'periods': ['2022'] if '2022' in question else ['2023']}, BASE)['companies'], [])

    def test_missing_context_does_not_invent_relative_year(self):
        intent = guard_intent('전년에는?', BASE, None)
        self.assertEqual(intent['periods'], [])
        self.assertEqual(intent['companies'], [])

    def test_clarification_only_requests_missing_field(self):
        answer = financial_answer({**BASE, 'periods': []}, json.loads(SNAPSHOT.read_text()))
        self.assertIn('회계연도', answer['answer_ko'])
        self.assertNotIn('지원 회사', answer['answer_ko'])
