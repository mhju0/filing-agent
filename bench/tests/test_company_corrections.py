import unittest
from slice.core import guard_intent

BASE = {"companies": ["Samsung"], "metric": "revenue", "periods": ["2023"], "basis": "consolidated", "action": "report"}


class CompanyCorrectionTests(unittest.TestCase):
    def test_basis_correction_does_not_exclude_company(self):
        for question in [
            "삼성전자 2023년 매출액을 연결 말고 별도 기준으로 보여줘.",
            "Samsung revenue in 2023, not consolidated but separate",
            "Samsung revenue in 2023, separate rather than consolidated",
        ]:
            guarded = guard_intent(question, {**BASE, "basis": "separate"}, None)
            self.assertEqual(guarded["companies"], ["Samsung"])
            self.assertEqual(guarded["basis"], "separate")

    def test_rejected_company_cannot_supply_unknown_target(self):
        for question in [
            "Not Samsung, but Tesla revenue in 2023?",
            "삼성이 아니라 테슬라 2023년 매출액은?",
            "Samsung 말고 Tesla revenue in 2023?",
            "Tesla revenue in 2023, not Samsung",
            "삼성이 아니고 테슬라의 2023년 매출액은?",
            "Tesla rather than Samsung revenue in 2023?",
            "삼성 대신 테슬라 2023년 매출액은?",
            "Tesla revenue in 2023, excluding Samsung",
            "Tesla revenue in 2023, unlike Samsung",
            "삼성 빼고 테슬라의 2023년 매출액은?",
            "삼성이 아니라 테슬라 2023년 매출액을 연결 말고 별도 기준으로 보여줘.",
            "No Samsung, Tesla revenue in 2023?",
            "Samsung isn't the company; Tesla revenue in 2023",
            "Samsung isn’t the company; Tesla revenue in 2023",
        ]:
            for companies in [[], ["Samsung"], ["NAVER"]]:
                with self.subTest(question=question, companies=companies):
                    guarded = guard_intent(question, {**BASE, "companies": companies}, BASE)
                    self.assertEqual(guarded["companies"], [])

    def test_explicit_same_company_followup_retains_context(self):
        for question in ["같은 회사의 2022년 수치를 보여줘.",
                         "Keep the same company and metric, but show FY2022."]:
            guarded = guard_intent(question, {**BASE, "periods": ["2022"]}, BASE)
            self.assertEqual(guarded["companies"], ["Samsung"])

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
