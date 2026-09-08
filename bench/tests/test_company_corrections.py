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
