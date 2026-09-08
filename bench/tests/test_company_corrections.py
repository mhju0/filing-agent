import unittest
from slice.core import guard_intent

BASE = {"companies": ["Samsung"], "metric": "revenue", "periods": ["2023"], "basis": "consolidated", "action": "report"}


class CompanyCorrectionTests(unittest.TestCase):
    def test_direct_correction_uses_named_target(self):
        for question in ["삼성전자가 아니라 네이버의 2023년 매출액을 알려줘.", "Not Samsung, but NAVER revenue in 2023?"]:
            self.assertEqual(guard_intent(question, BASE, None)["companies"], ["NAVER"])

    def test_conflicting_comparison_clarifies_instead_of_substituting(self):
        self.assertEqual(guard_intent("Compare Samsung and NAVER revenue in 2023", BASE, None)["companies"], [])

    def test_unknown_name_does_not_become_model_guess(self):
        self.assertEqual(guard_intent("Tesla revenue in 2023?", BASE, None)["companies"], [])

    def test_unknown_name_does_not_inherit_context(self):
        for question in ["Tesla revenue in 2023?", "테슬라 2023년 매출액은?"]:
            self.assertEqual(guard_intent(question, BASE, BASE)["companies"], [])

    def test_correction_with_further_company_mentions_clarifies(self):
        for question in ["Not Samsung, but NAVER and Samsung revenue in 2023?", "삼성이 아니라 네이버와 삼성의 2023년 매출액은?"]:
            self.assertEqual(guard_intent(question, BASE, BASE)["companies"], [])

    def test_bounded_followup_keeps_company(self):
        for question in ["What about 2023?", "그럼 2023년은?", "revenue in 2023?"]:
            self.assertEqual(guard_intent(question, BASE, BASE)["companies"], ["Samsung"])

    def test_correction_with_unknown_alternative_or_negation_clarifies(self):
        for question in ["Not Samsung, but NAVER or Tesla revenue in 2023?", "삼성이 아니라 네이버도 아닌 테슬라의 2023년 매출액을 알려줘."]:
            self.assertEqual(guard_intent(question, BASE, BASE)["companies"], [])

    def test_ambiguous_correction_clarifies_even_when_model_selects_both(self):
        model = {**BASE, "companies": ["Samsung", "NAVER"]}
        for question in ["Not Samsung, but NAVER or Tesla revenue in 2023?", "삼성이 아니라 네이버도 아닌 테슬라의 2023년 매출액을 알려줘."]:
            self.assertEqual(guard_intent(question, model, None)["companies"], [])
