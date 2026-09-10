import json
import unittest
from slice.core import SNAPSHOT, guard_intent
from slice.financial import financial_answer

BASE = {"companies": ["Samsung"], "metric": "revenue", "periods": ["2023"], "basis": "consolidated", "action": "report"}


class CompanyCorrectionTests(unittest.TestCase):
    def test_basis_correction_does_not_exclude_company(self):
        for question in [
            "삼성전자 2023년 매출액을 연결 말고 별도 기준으로 보여줘.",
            "삼성전자 2023년 매출액을 연결이 아닌 별도로 보여줘.",
            "삼성전자 2023년 매출액을 연결이 아니라 별도로 보여줘.",
            "삼성전자 2023년 매출액을 연결 대신 별도로 보여줘.",
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

    def test_supported_company_cannot_hide_unknown_comparison_company(self):
        questions = [
            "Compare Samsung and Tesla revenue in 2023",
            "Compare Rivian and Samsung automotive revenue in 2023",
            "Compare Samsung revenue with Tesla in 2023",
            "Compare revenue between TSLA and Samsung in 2023",
            "Samsung & Tesla revenue in 2023",
            "삼성전자와 테슬라의 2023년 매출액을 비교해줘.",
            "현대자동차와 삼성전자의 2023년 자동차 매출을 비교해줘.",
            "삼성 매출을 테슬라와 비교해줘.",
            "삼성전자 및 테슬라 2023년 매출액 비교",
        ]
        models = [
            {**BASE, "companies": ["Samsung"], "action": "report"},
            {**BASE, "companies": ["Samsung"], "action": "compare"},
        ]
        for question in questions:
            for model in models:
                with self.subTest(question=question, action=model["action"]):
                    self.assertEqual(guard_intent(question, model, None)["companies"], [])

    def test_unsupported_request_qualifier_does_not_become_supported_revenue(self):
        for question in [
            "Samsung automotive revenue in 2023",
            "삼성전자 2023년 자동차 부문 매출액은?",
        ]:
            with self.subTest(question=question):
                self.assertEqual(guard_intent(question, BASE, None)["companies"], [])

    def test_punctuation_does_not_create_an_unknown_company(self):
        for question in ["Samsung, revenue in 2023", "삼성전자, 2023년 매출액은?"]:
            with self.subTest(question=question):
                self.assertEqual(guard_intent(question, BASE, None)["companies"], ["Samsung"])

    def test_supported_request_starters_and_output_instruction_remain_bounded(self):
        cases = [
            ("삼성전자 2023년과 2022년 매출액을 비교해 줘",
             {**BASE, "periods": ["2022", "2023"], "action": "compare"}),
            ("Microsoft 2024년과 2023년 당기순이익을 비교해 줘",
             {**BASE, "companies": ["Microsoft"], "metric": "net_income",
              "periods": ["2023", "2024"], "action": "compare"}),
            ("Samsung revenue in 2023. Answer in Korean.", BASE),
            ("삼성전자가 2023년에 보고한 매출액을 확인하고 싶어.", BASE),
            ("How much did Samsung spend on R&D in fiscal 2023?",
             {**BASE, "metric": "research_and_development"}),
            ("For Samsung fiscal 2023, use separate statements for revenue.",
             {**BASE, "basis": "separate"}),
            ("The company I meant is Samsung.", BASE),
            ("Samsung Electronics revenue in 2023", BASE),
        ]
        for question, model in cases:
            with self.subTest(question=question):
                self.assertEqual(
                    guard_intent(question, model, None)["companies"],
                    model["companies"],
                )

    def test_unknown_scope_after_sentence_boundary_is_not_ignored(self):
        for question in [
            "Samsung revenue in 2023. Compare it with Tesla.",
            "삼성전자 2023년 매출액은? 테슬라와도 비교해줘.",
        ]:
            with self.subTest(question=question):
                self.assertEqual(guard_intent(question, BASE, None)["companies"], [])

    def test_mixed_company_request_clarifies_without_partial_report(self):
        question = "Compare Samsung and Tesla revenue in 2023"
        guarded = guard_intent(question, BASE, None)
        answer = financial_answer(guarded, json.loads(SNAPSHOT.read_text()), question)
        self.assertEqual(answer["operation"], "clarify")
        self.assertEqual(answer["reason_code"], "ambiguous_context")
        self.assertEqual(answer["figures"], [])
        self.assertEqual(answer["fact_ids"], [])

    def test_two_supported_companies_remain_available_to_policy(self):
        model = {**BASE, "companies": ["Samsung", "NAVER"], "action": "compare"}
        for question in [
            "Compare Samsung and NAVER revenue in 2023",
            "삼성전자와 네이버의 2023년 매출액을 비교해줘.",
        ]:
            with self.subTest(question=question):
                self.assertEqual(
                    guard_intent(question, model, None)["companies"],
                    ["Samsung", "NAVER"],
                )

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
