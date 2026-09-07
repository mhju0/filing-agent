import copy
import io
import json
import os
import sys
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run
from scoring import expected_figures, score

CASES = json.loads((run.ROOT / "cases.json").read_text())
FIXTURES = {name: json.loads((run.ROOT / "fixtures" / name).read_text())
            for name in ("samsung_is.json", "naver_is.json")}


def oracle(turn):
    expected = turn["expected"]
    figures = expected_figures(FIXTURES[turn["fixture"]], expected)
    result = {"answer_ko": "제공된 근거에 요청한 수치가 없습니다." if expected["refused"] else "공시 수치를 확인했습니다.",
              "answer_en": "The supplied evidence does not contain that figure." if expected["refused"] else "The reported figures are shown.",
              "figures": figures, "calculated": [], "refused": expected["refused"],
              "refusal_reason": "제공된 표에 해당 항목이 없습니다." if expected["refused"] else None}
    for calc in expected["calculated"]:
        result["calculated"].append({"label": calc["label"], "formula": calc["formula"],
                                     "value": calc["value"], "inputs": copy.deepcopy(figures)})
    return result


def slow_worker(connection, payload, timeout):
    time.sleep(3)


class ScoringTests(unittest.TestCase):
    def assess(self, turn, answer):
        content = answer if isinstance(answer, str) else json.dumps(answer, ensure_ascii=False)
        return score(content, FIXTURES[turn["fixture"]], turn["expected"], turn["question"])

    def test_all_exact_oracles_pass(self):
        for case in CASES:
            for turn in case["turns"]:
                with self.subTest(case=case["id"], question=turn["question"]):
                    self.assertTrue(self.assess(turn, oracle(turn))["accuracy"])

    def test_correct_calculated_number_not_hallucinated(self):
        turn = CASES[0]["turns"][0]
        answer = oracle(turn)
        answer["answer_ko"] = "증감률은 -14.33%입니다."
        scored = self.assess(turn, answer)
        self.assertTrue(scored["accuracy"])
        self.assertIn("-14.33", scored["novel_numbers"])
        self.assertEqual(scored["invented_numbers"], [])

    def test_wrong_formula_or_operands_fail(self):
        turn = CASES[0]["turns"][0]
        for kind in ("formula", "operand", "value"):
            answer = oracle(turn)
            calc = answer["calculated"][0]
            if kind == "formula":
                calc["formula"] = "(258935494 - 302231360) / 258935494 * 100"
            elif kind == "operand":
                calc["inputs"][0]["source"]["company"] = "네이버"
            else:
                calc["value"] = "14.33"
            self.assertFalse(self.assess(turn, answer)["accuracy"])

    def test_wrong_source_period_unit_or_company_fails(self):
        turn = CASES[1]["turns"][1]
        for kind in ("source", "period", "unit", "company"):
            answer = oracle(turn)
            figure = answer["figures"][0]
            if kind == "source":
                figure["source"]["section"] = "연결재무상태표"
            elif kind == "company":
                figure["source"]["company"] = "삼성전자"
            else:
                figure[kind] = "2022" if kind == "period" else "원"
            self.assertFalse(self.assess(turn, answer)["figure_exact_match"])

    def test_invented_number_in_prose_caught_verbatim(self):
        turn = CASES[1]["turns"][0]
        answer = oracle(turn)
        answer["answer_en"] = "Research expenses were 12,345.67 million KRW."
        scored = self.assess(turn, answer)
        self.assertEqual(scored["invented_numbers"], ["12,345.67"])
        self.assertFalse(scored["accuracy"])

    def test_missing_disallows_other_supplied_figures_and_zero(self):
        turn = CASES[2]["turns"][0]
        for value in ("0", "258935494"):
            answer = oracle(turn)
            answer["answer_ko"] = f"연구개발비는 {value} 백만원입니다."
            scored = self.assess(turn, answer)
            self.assertTrue(scored["refusal_violation"])
            self.assertFalse(scored["accuracy"])

    def test_false_refusal_fails(self):
        turn = CASES[1]["turns"][0]
        answer = oracle(CASES[2]["turns"][0])
        self.assertFalse(self.assess(turn, answer)["refusal_correct"])

    def test_extra_figures_and_wrong_value_fail(self):
        turn = CASES[1]["turns"][0]
        answer = oracle(turn)
        answer["figures"].append(copy.deepcopy(answer["figures"][0]))
        self.assertFalse(self.assess(turn, answer)["accuracy"])
        answer = oracle(turn)
        answer["figures"][0]["value"] = "302231360"
        self.assertFalse(self.assess(turn, answer)["accuracy"])

    def test_invalid_strict_json_rejected(self):
        turn = CASES[2]["turns"][0]
        for content in ('```json\n{}\n```', '{"refused":true,"refused":false}', '{"value":NaN}', '[]'):
            self.assertFalse(self.assess(turn, content)["accuracy"])

    def test_no_fixture_has_deliberately_missing_metric(self):
        for fixture in FIXTURES.values():
            self.assertNotIn("연구개발비", [row["label"] for row in fixture["rows"]])
            self.assertTrue(15 <= len(fixture["rows"]) <= 18)


class HarnessTests(unittest.TestCase):
    def response(self, payload, timeout):
        question = payload["messages"][-1]["content"].split("\nQUESTION:\n")[1]
        turn = next(t for c in CASES for t in c["turns"] if t["question"] == question)
        return {"wall_seconds": 0.01, "response": {"message": {"content": json.dumps(oracle(turn), ensure_ascii=False)},
                 "done": True, "done_reason": "stop", "eval_count": 10, "eval_duration": 1000000000}}

    def test_switch_preserves_actual_prior_answer(self):
        seen = []
        def answer(payload, timeout):
            seen.append(copy.deepcopy(payload))
            response = self.response(payload, timeout)
            if len(seen) == 1:
                response["response"]["message"]["content"] = '{"wrong": 987654321}'
            return response
        with patch.object(run, "timed_chat", side_effect=answer):
            trial = run.run_trial("test:local", CASES[1], FIXTURES, "system", True)
        self.assertEqual(seen[1]["messages"][-2]["content"], '{"wrong": 987654321}')
        self.assertIn('"company": "네이버"', seen[1]["messages"][-1]["content"])
        self.assertFalse(trial["accuracy"])
        self.assertEqual(seen[0]["keep_alive"], 0)
        self.assertFalse(seen[0]["think"])

    def test_wall_deadline_terminates_worker(self):
        start = time.monotonic()
        result = run.timed_chat({}, .3, worker=slow_worker)
        self.assertTrue(result["timeout"])
        self.assertLess(time.monotonic() - start, 2)

    def test_cloud_or_unverifiable_models_rejected(self):
        for name, info in [("qwen:cloud", {"model_info": {"general.architecture": "qwen"}}),
                           ("local:tag", {"remote_host": "https://example.com"}),
                           ("local:tag", {"model_info": {}})]:
            with patch.object(run, "api", return_value=info), self.assertRaises(ValueError):
                run.local_model_info(name)

    def test_defaults_include_installed_exaone_exact_tag(self):
        with patch.dict(os.environ, {"MODELS": ""}):
            self.assertEqual(run.select_models(["exaone3.5:7.8b", "other:latest"]),
                             ["qwen3:8b", "gemma4:e4b", "exaone3.5:7.8b"])

    def test_http_redirects_and_environment_proxies_are_disabled(self):
        from unittest.mock import MagicMock
        session = MagicMock()
        session.request.return_value.status_code = 302
        with patch.object(run.requests, "Session") as constructor:
            constructor.return_value.__enter__.return_value = session
            with self.assertRaises(RuntimeError):
                run.api("GET", "/api/tags")
        self.assertFalse(session.trust_env)
        self.assertFalse(session.request.call_args.kwargs["allow_redirects"])
        self.assertEqual(session.request.call_args.args[1], "http://127.0.0.1:11434/api/tags")

    def test_missing_fabrication_disqualifies_and_quotes_amount(self):
        captured = []
        def fake_api(method, path, payload=None):
            if path == "/api/tags":
                return {"models": [{"name": "test:local", "size": 1000}]}
            if path == "/api/version":
                return {"version": "test-only"}
            return {"model_info": {"general.architecture": "test"}}
        def fabricate(payload, timeout):
            response = self.response(payload, timeout)
            if "연구개발비" in payload["messages"][-1]["content"]:
                answer = json.loads(response["response"]["message"]["content"])
                answer["answer_en"] = "The expense was 999,888.77 million KRW."
                response["response"]["message"]["content"] = json.dumps(answer)
            return response
        with patch.object(run, "api", side_effect=fake_api), \
             patch.object(run, "timed_chat", side_effect=fabricate), \
             patch.object(run, "save", side_effect=lambda result: captured.append(copy.deepcopy(result))), \
             patch.dict(os.environ, {"MODELS": "test:local"}), redirect_stdout(io.StringIO()):
            run.main()
        self.assertIn("DISQUALIFIED", captured[-1]["model_verdicts"]["test:local"])
        self.assertIn('`999,888.77`', run.markdown(captured[-1]))

    def test_timeout_halts_remaining_generation(self):
        captured = []
        def fake_api(method, path, payload=None):
            if path == "/api/tags":
                return {"models": [{"name": "test:local", "size": 1000}]}
            if path == "/api/version":
                return {"version": "test-only"}
            return {"model_info": {"general.architecture": "test"}}
        with patch.object(run, "api", side_effect=fake_api), \
             patch.object(run, "timed_chat", return_value={"error": "deadline", "timeout": True, "wall_seconds": 120}) as chat, \
             patch.object(run, "save", side_effect=lambda result: captured.append(copy.deepcopy(result))), \
             patch.dict(os.environ, {"MODELS": "test:local"}), redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(), 2)
        self.assertEqual(chat.call_count, 1)
        self.assertEqual(captured[-1]["attempted_trials"], 1)
        self.assertEqual(captured[-1]["status"], "partial")

    def test_unavailable_runtime_records_unrun_not_incorrect(self):
        captured = []
        with patch.object(run, "api", side_effect=run.requests.ConnectionError("test runtime unavailable")), \
             patch.object(run, "save", side_effect=lambda result: captured.append(copy.deepcopy(result))), \
             patch.dict(os.environ, {"MODELS": ""}), redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(), 2)
        result = captured[-1]
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["attempted_trials"], 0)
        self.assertIn("N/A (0/3 run)", run.markdown(result))

    def test_end_to_end_control_flow_without_model_calls(self):
        captured = []
        def fake_api(method, path, payload=None):
            if path == "/api/tags":
                return {"models": [{"name": "test:local", "size": 1000, "digest": "test-digest"}]}
            if path == "/api/version":
                return {"version": "test-only"}
            return {"model_info": {"general.architecture": "test"}, "capabilities": ["completion"]}
        with patch.object(run, "api", side_effect=fake_api), \
             patch.object(run, "timed_chat", side_effect=self.response), \
             patch.object(run, "save", side_effect=lambda result: captured.append(copy.deepcopy(result))), \
             patch.dict(os.environ, {"MODELS": "test:local"}), redirect_stdout(io.StringIO()):
            self.assertEqual(run.main(), 0)
        result = captured[-1]
        self.assertEqual(result["attempted_trials"], 9)
        self.assertTrue(all(r["accuracy"] for e in result["results"] for r in e["runs"]))
        self.assertIn("passed 3/3", result["model_verdicts"]["test:local"])
        self.assertIn("0.00", run.markdown(result))


if __name__ == "__main__":
    unittest.main()
