import copy
import threading
import time
import unittest

import psycopg

from slice.store import Store
from slice.workflow import Engine
from test_slice import Runtime


class FaultStore(Store):
    def __init__(self):
        super().__init__()
        self.fail = set()
        self.complete_seen = threading.Event()
        self.allow_complete = threading.Event()
        self.allow_complete.set()
        self.final_candidates = []
        self.uncertain = False

    def change(self, identity, fn):
        def intercept(body):
            fn(body)
            turn = body['turns'][-1] if body['turns'] else {}
            if turn.get('status') in ('complete', 'discarded'):
                self.final_candidates.append(copy.deepcopy(turn))
                self.complete_seen.set()
                self.allow_complete.wait(5)
                if identity in self.fail:
                    raise psycopg.OperationalError('Injected final-write failure')
        result = super().change(identity, intercept)
        if self.uncertain and result['turns'][-1]['status'] == 'complete':
            self.uncertain = False
            raise psycopg.OperationalError('Commit succeeded; acknowledgement lost')
        return result


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.store = FaultStore()
        self.store.setup()
        self.runtime = Runtime()
        self.engine = Engine(self.store, self.runtime)
        self.ids = []

    def tearDown(self):
        self.store.allow_complete.set()
        self.wait()
        self.engine.pool.close()
        with self.store.connect() as db:
            for identity in self.ids:
                db.execute('DELETE FROM investigations WHERE id=%s', (identity,))
                for table in ('checkpoints', 'checkpoint_blobs', 'checkpoint_writes'):
                    db.execute(f'DELETE FROM {table} WHERE thread_id=%s', (identity,))

    def create(self):
        inv = self.engine.investigations.create()
        self.ids.append(inv['id'])
        return inv['id']

    def submit(self, identity):
        return self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()))

    def wait(self):
        deadline = time.monotonic() + 8
        while self.engine.gate.locked() and time.monotonic() < deadline:
            time.sleep(.01)
        self.assertFalse(self.engine.gate.locked(), 'Persistence failure must not retain the execution gate')

    def test_completion_contains_timing_and_delete_cannot_cross_finalization(self):
        identity = self.create()
        self.store.allow_complete.clear()
        self.submit(identity)
        self.assertTrue(self.store.complete_seen.wait(5))
        durable = Store().get(identity)
        self.assertEqual(durable['turns'][-1]['status'], 'saving')
        deleted = threading.Event()
        def delete():
            Store().delete(identity)
            deleted.set()
        worker = threading.Thread(target=delete)
        worker.start()
        self.assertFalse(deleted.wait(.05))
        self.assertIn('wall_seconds', self.store.final_candidates[-1])
        self.store.allow_complete.set()
        worker.join(5)
        self.assertTrue(deleted.is_set())
        self.wait()
        self.assertEqual(self.engine.events, {})

    def test_storage_retries_preserve_result_context_and_single_inference(self):
        identity = self.create()
        self.store.fail.add(identity)
        first = self.submit(identity)
        self.wait()
        inv = self.engine.investigations.get(identity)
        self.assertEqual(inv['turns'][-1]['status'], 'storage_failed')
        self.assertTrue(inv['turns'][-1]['answer']['figures'])
        self.assertIsNone(inv['accepted'])
        self.assertEqual(self.engine.events, {})
        for _ in range(2):
            with self.assertRaises(ValueError):
                self.engine.retry_storage(identity)
        for action in [lambda: self.submit(identity), lambda: self.engine.investigations.save(identity),
                       lambda: self.engine.investigations.create(identity, 'continue')]:
            with self.assertRaises(ValueError):
                action()
        other = self.create()
        self.submit(other)
        self.wait()
        self.store.fail.clear()
        restored = self.engine.retry_storage(identity)
        self.assertEqual([t['id'] for t in restored['turns']], [first['id']])
        self.assertEqual(restored['turns'][0]['status'], 'complete')
        self.assertIsNotNone(restored['accepted'])
        self.assertEqual(len(self.runtime.contexts), 2)
        with self.assertRaises(ValueError):
            self.engine.retry_storage(identity)

    def test_uncertain_commit_retries_without_duplicating_turn(self):
        identity = self.create()
        self.store.uncertain = True
        first = self.submit(identity)
        self.wait()
        self.assertEqual(self.engine.investigations.get(identity)['turns'][-1]['status'], 'storage_failed')
        inv = self.engine.retry_storage(identity)
        self.assertEqual([t['id'] for t in inv['turns']], [first['id']])
        self.assertEqual(len(self.runtime.contexts), 1)

    def test_discard_requires_durable_resolution_and_keeps_previous_context(self):
        identity = self.create()
        self.submit(identity)
        self.wait()
        prior = self.store.get(identity)
        self.store.fail.add(identity)
        self.submit(identity)
        self.wait()
        with self.assertRaises(ValueError):
            self.engine.retry_storage(identity, discard=True)
        self.assertEqual(self.engine.investigations.get(identity)['turns'][-1]['status'], 'storage_failed')
        self.store.fail.clear()
        inv = self.engine.retry_storage(identity, discard=True)
        self.assertEqual(inv['accepted'], prior['accepted'])
        self.assertEqual(inv['turns'][:-1], prior['turns'])
        self.assertEqual(inv['turns'][-1]['status'], 'discarded')
        self.assertNotIn('answer', inv['turns'][-1])

    def test_restart_recovers_only_durable_receipts(self):
        identity = self.create()
        self.store.fail.add(identity)
        self.submit(identity)
        self.wait()
        self.store.fail.clear()
        self.assertTrue(self.store.recover())
        recovered = self.store.get(identity)['turns'][-1]
        self.assertEqual(recovered['status'], 'interrupted')
        self.assertIn('answer', recovered)
        self.assertNotIn('wall_seconds', recovered)
