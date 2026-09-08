import copy
import json
import time
import unittest

from psycopg.types.json import Jsonb

from slice.core import SNAPSHOT, financial_answer, guard_intent
from slice.export import recording
from slice.runtime import Stopped
from slice.store import Store, uid
from slice.workflow import Engine

BASE = {
    "companies": ["Samsung"],
    "metric": "revenue",
    "periods": ["2023"],
    "basis": "consolidated",
    "action": "report",
}


class Runtime:
    def __init__(self, intent=None, stop=False):
        self.intent = intent or BASE
        self.contexts = []
        self.stop = stop

    def interpret(self, question, context, cancel):
        self.contexts.append(copy.deepcopy(context))
        if self.stop:
            cancel.wait(3)
            raise Stopped(True)
        return copy.deepcopy(self.intent), {
            "content": json.dumps(self.intent),
            "model": "TEST DOUBLE; NOT REPLAY EVIDENCE",
        }


class SliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = Store()
        cls.store.setup()

    def setUp(self):
        self.ids = []

    def new(self):
        data = self.store.create()
        self.ids.append(data["id"])
        return data

    def tearDown(self):
        with self.store.connect() as db:
            for identity in self.ids:
                db.execute("DELETE FROM investigations WHERE id=%s", (identity,))

    def wait(self, engine, identity):
        deadline = time.monotonic() + 10
        while engine.gate.locked() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertFalse(engine.gate.locked())
        return self.store.get(identity)

    def test_clarification_survives_store_recreation_without_accepting_partial(self):
        inv = self.new()
        runtime = Runtime({**BASE, "companies": []})
        engine = Engine(self.store, runtime)
        engine.submit(inv["id"], "2023 매출액", "ko", uid())
        data = self.wait(engine, inv["id"])
        self.assertIsNone(data["accepted"])
        self.assertEqual(data["pending"]["periods"], ["2023"])
        runtime.intent = BASE
        engine = Engine(Store(), runtime)
        engine.submit(inv["id"], "삼성전자", "ko", uid())
        data = self.wait(engine, inv["id"])
        self.assertEqual(runtime.contexts[-1]["metric"], "revenue")
        self.assertIsNone(data["pending"])
        self.assertEqual(data["accepted"], BASE)

    def test_save_continue_and_refresh_preserve_original(self):
        inv = self.new()
        engine = Engine(self.store, Runtime())
        engine.submit(inv["id"], "Samsung 2023 revenue", "en", uid())
        self.wait(engine, inv["id"])
        frozen = self.store.save(inv["id"])
        with self.assertRaises(ValueError):
            engine.submit(inv["id"], "NAVER?", "en", uid())
        continued = self.store.create(inv["id"], "continue")
        self.ids.append(continued["id"])
        refreshed = self.store.create(inv["id"], "refresh")
        self.ids.append(refreshed["id"])
        self.assertEqual(continued["turns"], frozen["turns"])
        self.assertEqual(continued["snapshot_id"], frozen["snapshot_id"])
        self.assertEqual(refreshed["turns"], [])
        self.assertEqual(self.store.get(inv["id"]), frozen)

    def test_duplicate_request_and_serial_execution(self):
        inv = self.new()
        runtime = Runtime(stop=True)
        engine = Engine(self.store, runtime)
        rid = uid()
        first = engine.submit(inv["id"], "Samsung 2023 revenue", "en", rid)
        duplicate = engine.submit(inv["id"], "Samsung 2023 revenue", "en", rid)
        self.assertEqual(first["id"], duplicate["id"])
        with self.assertRaises(ValueError):
            engine.submit(inv["id"], "NAVER?", "en", uid())
        engine.cancel(first["id"])
        data = self.wait(engine, inv["id"])
        self.assertEqual(data["turns"][-1]["status"], "cancelled")
        self.assertIsNone(data["accepted"])

    def test_interrupted_step_reuses_only_completed_evidence_and_one_retry(self):
        inv = self.new()
        answer = financial_answer(BASE, self.store.snapshot(inv["snapshot_id"]))
        failed = {
            "id": uid(),
            "request_id": uid(),
            "question": "Samsung 2023 revenue",
            "language": "en",
            "status": "running",
            "context": None,
            "intent": BASE,
            "answer": answer,
            "model_record": {"content": "test"},
            "steps": [
                {"name": "interpret", "status": "complete"},
                {"name": "evidence", "status": "complete"},
                {"name": "answer", "status": "running"},
            ],
        }
        self.store.change(inv["id"], lambda body: body["turns"].append(failed))
        self.store.recover()
        self.assertEqual(self.store.get(inv["id"])["turns"][0]["status"], "interrupted")
        runtime = Runtime()
        engine = Engine(self.store, runtime)
        engine.submit(inv["id"], failed["question"], "en", uid(), retry=failed["id"])
        data = self.wait(engine, inv["id"])
        self.assertEqual(runtime.contexts, [])
        self.assertEqual(data["turns"][-1]["answer"], answer)
        with self.assertRaises(ValueError):
            engine.submit(
                inv["id"], failed["question"], "en", uid(), retry=failed["id"]
            )

    def test_snapshot_missing_does_not_silently_refresh(self):
        inv = self.new()
        self.store.change(inv["id"], lambda b: b.update(snapshot_id="missing"))
        with self.assertRaises(ValueError):
            self.store.create(inv["id"], "continue")

    def test_unknown_is_not_zero_or_wrong_company(self):
        snap = json.loads(SNAPSHOT.read_text())
        answer = financial_answer({**BASE, "metric": "research_and_development"}, snap)
        self.assertEqual(answer["figures"], [])
        self.assertTrue(answer["refused"])
        guessed = guard_intent("2023년 매출액은?", BASE, None)
        self.assertEqual(guessed["companies"], [])
        self.assertEqual(financial_answer(guessed, snap)["operation"], "clarify")
        self.assertEqual(guard_intent("네이버는?", BASE, BASE)["companies"], ["NAVER"])
        with self.assertRaises(ValueError):
            guard_intent(
                "2022년은?",
                {**BASE, "companies": ["Samsung"], "periods": ["2022"]},
                {**BASE, "companies": ["NAVER"]},
            )

    def test_expiry_does_not_delete_saved(self):
        ordinary = self.new()
        saved = self.new()
        for inv in (ordinary, saved):
            inv["touched_at"] = "2000-01-01T00:00:00+00:00"
        saved["saved"] = True
        with self.store.connect() as db:
            for inv in (ordinary, saved):
                db.execute(
                    "UPDATE investigations SET body=%s WHERE id=%s",
                    (Jsonb(inv), inv["id"]),
                )
        with self.assertRaisesRegex(ValueError, "expired"):
            self.store.get(ordinary["id"])
        self.assertEqual(self.store.get(saved["id"])["id"], saved["id"])
        ids = [i["id"] for i in self.store.history()]
        self.assertNotIn(ordinary["id"], ids)
        self.assertIn(saved["id"], ids)

    def test_export_refuses_uncaptured_or_unsaved_results(self):
        with self.assertRaises(ValueError):
            recording([self.new()])

    def test_host_origin_and_token_protect_mutations(self):
        from fastapi.testclient import TestClient

        from slice.app import app

        with TestClient(app, base_url="http://127.0.0.1:8765") as client:
            self.assertEqual(
                client.post("/api/investigations", json={}).status_code, 403
            )
            self.assertEqual(
                client.get(
                    "/api/session", headers={"host": "evil.example"}
                ).status_code,
                403,
            )
            self.assertEqual(
                client.get(
                    "/api/session", headers={"origin": "https://evil.example"}
                ).status_code,
                403,
            )
            self.assertEqual(
                client.get(
                    "/api/session", headers={"sec-fetch-site": "cross-site"}
                ).status_code,
                403,
            )
            response = client.get("/api/session")
            self.assertEqual(response.status_code, 200)
            self.assertIn(
                "connect-src 'self'", response.headers["content-security-policy"]
            )

    def test_every_pilot_fact_roundtrips_and_partial_never_substitutes(self):
        from slice.core import catalog

        snapshot = json.loads(SNAPSHOT.read_text())
        for fact in catalog(snapshot):
            answer = financial_answer(
                {
                    **BASE,
                    "companies": [fact["company"]],
                    "metric": fact["metric"],
                    "periods": [fact["period"]],
                },
                snapshot,
            )
            self.assertEqual(answer["figures"][0]["value"], fact["value"])
            self.assertTrue(answer["searched"])
        partial = financial_answer(
            {**BASE, "periods": ["2021", "2023"], "action": "compare"}, snapshot
        )
        self.assertEqual([f["period"] for f in partial["figures"]], ["2023"])
        self.assertEqual(partial["calculated"], [])
        self.assertTrue(partial["partial"])

    def test_private_backup_restore_and_diagnostic_expiry(self):
        import tempfile
        from pathlib import Path

        from slice.backup import backup, restore

        inv = self.new()
        engine = Engine(self.store, Runtime())
        engine.submit(inv["id"], "Samsung 2023 revenue", "en", uid())
        data = self.wait(engine, inv["id"])
        self.assertNotIn("content", data["turns"][0]["model_record"])
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "backup.json"
            backup(p)
            before = {i["id"] for i in self.store.history()}
            restored = restore(p)
            self.ids.extend(restored)
            self.assertFalse(set(restored) & before)
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                backup(p)
            body = json.loads(p.read_text())
            body["investigations"][0]["snapshot_id"] = "changed"
            p.write_text(json.dumps(body))
            with self.assertRaises(ValueError):
                restore(p)
        self.store.delete(inv["id"])
        with self.assertRaises(ValueError):
            self.store.get(inv["id"])

    def test_native_graph_checkpoints_survive_new_engine_and_delete(self):
        inv = self.new()
        engine = Engine(self.store, Runtime())
        engine.submit(inv["id"], "Samsung 2023 revenue", "en", uid())
        self.wait(engine, inv["id"])
        config = {"configurable": {"thread_id": inv["id"]}}
        state = engine.graph.get_state(config)
        self.assertEqual(state.values["last_completed"], "answer")
        self.assertEqual(state.next, ())
        second = Engine(Store(), Runtime())
        self.assertEqual(second.graph.get_state(config).values, state.values)
        self.store.delete(inv["id"])
        self.assertEqual(second.graph.get_state(config).values, {})
        engine.pool.close()
        second.pool.close()
