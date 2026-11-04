import copy
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import psycopg

from slice.store import Store
from slice.workflow import Engine
from slice.lifecycle import StorageUnavailable
from slice.export import recording
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
        self.queue_fault = None
        self.unavailable = False
        self.receipt_fail = set()
        self.read_unavailable = False
        self.interrupted_fail = set()

    def get(self, identity):
        if self.read_unavailable:
            raise psycopg.OperationalError('Injected unavailable readback')
        return super().get(identity)

    def change(self, identity, fn):
        if self.unavailable:
            raise psycopg.OperationalError('Injected unavailable storage')
        def intercept(body):
            fn(body)
            turn = body['turns'][-1] if body['turns'] else {}
            if identity in self.interrupted_fail and turn.get('status') == 'interrupted':
                raise psycopg.OperationalError('Injected dispatch-failure receipt error')
            if identity in self.receipt_fail and 'model_record' in turn:
                raise psycopg.OperationalError('Injected first diagnostic-receipt failure')
            if self.queue_fault == 'before' and turn.get('status') == 'queued':
                self.queue_fault = None
                raise psycopg.OperationalError('Queue transaction rolled back')
            if turn.get('status') in ('complete', 'discarded'):
                self.final_candidates.append(copy.deepcopy(turn))
                self.complete_seen.set()
                self.allow_complete.wait(5)
                if identity in self.fail:
                    raise psycopg.OperationalError('Injected final-write failure')
        result = super().change(identity, intercept)
        if self.queue_fault == 'after' and result['turns'][-1]['status'] == 'queued':
            self.queue_fault = None
            raise psycopg.OperationalError('Queue committed; acknowledgement lost')
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

    def test_initial_enqueue_failure_has_durable_recovery_without_inference(self):
        for fault in ('before', 'after'):
            with self.subTest(fault=fault):
                identity = self.create()
                request_id = str(time.time_ns())
                self.store.queue_fault = fault
                with self.assertRaises(StorageUnavailable):
                    self.engine.submit(identity, 'Samsung 2023 revenue', 'en', request_id)
                failed = self.engine.investigations.get(identity)['turns'][-1]
                self.assertEqual(failed['status'], 'storage_failed')
                repeated = self.engine.submit(identity, 'Samsung 2023 revenue', 'en', request_id)
                self.assertEqual(repeated['id'], failed['id'])
                self.assertEqual(repeated['status'], 'storage_failed')
                self.assertEqual(self.engine.events, {})
                self.assertFalse(self.engine.gate.locked())
                calls = len(self.runtime.contexts)
                self.store.unavailable = True
                with self.assertRaises(StorageUnavailable):
                    self.engine.retry_storage(identity)
                self.assertEqual(self.engine.investigations.get(identity)['turns'][-1]['status'],
                                 'storage_failed')
                self.store.unavailable = False
                recovered = self.engine.retry_storage(identity)
                self.assertEqual([t['id'] for t in recovered['turns']], [failed['id']])
                self.assertEqual(recovered['turns'][-1]['status'], 'interrupted')
                self.assertEqual(len(self.runtime.contexts), calls)
                self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                                   retry=failed['id'])
                self.wait()
                durable = self.store.get(identity)
                self.assertEqual(len(durable['turns']), 2)
                self.assertEqual(durable['turns'][-1]['status'], 'complete')
                self.assertEqual(len(self.runtime.contexts), calls + 1)

    def test_duplicate_submit_after_stale_read_does_not_execute_twice(self):
        self.duplicate_submit_after_stale_read('Samsung 2023 revenue')

    def test_conflicting_duplicate_after_stale_read_is_rejected(self):
        self.duplicate_submit_after_stale_read('NAVER 2023 revenue')

    def duplicate_submit_after_stale_read(self, duplicate_question):
        identity = self.create()
        question, request_id = 'Samsung 2023 revenue', str(time.time_ns())
        reached_gate, release = threading.Event(), threading.Event()
        original_gate = self.engine.gate

        class PausedGate:
            def acquire(self, blocking=False):
                if threading.current_thread().name == 'duplicate-submit':
                    reached_gate.set()
                    if not release.wait(5):
                        raise AssertionError('Duplicate submit was not released')
                return original_gate.acquire(blocking=blocking)

            def release(self):
                original_gate.release()

            def locked(self):
                return original_gate.locked()

        self.engine.gate = PausedGate()
        results, errors = [], []

        def duplicate():
            try:
                results.append(self.engine.submit(identity, duplicate_question, 'en', request_id))
            except Exception as exc:
                errors.append(exc)

        worker = threading.Thread(target=duplicate, name='duplicate-submit')
        worker.start()
        try:
            self.assertTrue(reached_gate.wait(5))
            first = self.engine.submit(identity, question, 'en', request_id)
            self.wait()
            completed = self.store.get(identity)
        finally:
            release.set()
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.wait()
        self.assertEqual([t['id'] for t in self.store.get(identity)['turns']], [first['id']])
        self.assertEqual(self.store.get(identity), completed)
        if duplicate_question == question:
            self.assertEqual(errors, [])
            self.assertEqual([t['id'] for t in results], [first['id']])
        else:
            self.assertEqual(results, [])
            self.assertEqual(len(errors), 1)
            self.assertIsInstance(errors[0], ValueError)
            self.assertIn('different inputs', str(errors[0]))
        self.assertEqual(len(self.runtime.contexts), 1)

    def test_expired_diagnostics_are_not_served_or_restored_by_storage_retry(self):
        identity = self.create()
        self.store.fail.add(identity)
        self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                           diagnostics=True)
        self.wait()
        cached = self.engine.investigations.working[identity]['turns'][-1]
        self.assertIn('content', cached['model_record'])
        created_at = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        cached['created_at'] = created_at
        self.store.fail.clear()
        self.store.change(identity, lambda body: body['turns'][-1].update(created_at=created_at))
        self.store.expire_diagnostics()
        self.assertNotIn('content', self.store.get(identity)['turns'][-1]['model_record'])
        visible = self.engine.investigations.get(identity)['turns'][-1]
        with self.subTest(surface='cached read'):
            self.assertNotIn('content', visible['model_record'])
        restored = self.engine.retry_storage(identity)['turns'][-1]
        with self.subTest(surface='storage retry'):
            self.assertNotIn('content', restored['model_record'])
            self.assertNotIn('content', self.store.get(identity)['turns'][-1]['model_record'])

    def test_manual_diagnostics_clear_covers_unstored_first_receipt(self):
        identity = self.create()
        self.store.receipt_fail.add(identity)
        self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                           diagnostics=True)
        self.wait()
        cached = self.engine.investigations.get(identity)['turns'][-1]
        self.assertIn('content', cached['model_record'])
        self.assertNotIn('model_record', self.store.get(identity)['turns'][-1])
        self.store.read_unavailable = True
        try:
            self.assertNotIn('content', self.engine.investigations.get(identity)['turns'][-1]['model_record'])
        finally:
            self.store.read_unavailable = False
        Store().expire_diagnostics(immediate=True)
        with self.subTest(surface='cached read'):
            self.assertNotIn('content', self.engine.investigations.get(identity)['turns'][-1]['model_record'])
        self.store.receipt_fail.clear()
        restored = self.engine.retry_storage(identity)['turns'][-1]
        with self.subTest(surface='storage retry'):
            self.assertNotIn('content', restored['model_record'])

    def test_diagnostic_clear_marker_stays_out_of_public_recording(self):
        identity = self.create()
        self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                           diagnostics=True)
        self.wait()
        Store().expire_diagnostics(immediate=True)
        saved = self.engine.investigations.save(identity)
        self.assertTrue(saved['turns'][-1]['diagnostics_cleared'])
        exported = recording([saved])['investigations'][0]['turns'][0]
        self.assertNotIn('diagnostics_cleared', exported)
        self.assertNotIn('model_record', exported)

    def test_initial_enqueue_recovery_refuses_changed_or_saved_investigation(self):
        for update in ({'saved': True}, {'accepted': {'companies': ['NAVER']}},
                       {'snapshot_id': 'different'}):
            with self.subTest(update=update):
                identity = self.create()
                self.store.queue_fault = 'before'
                with self.assertRaises(StorageUnavailable):
                    self.submit(identity)
                self.store.change(identity, lambda body: body.update(update))
                before = self.store.get(identity)
                with self.assertRaises(StorageUnavailable):
                    self.engine.retry_storage(identity)
                self.assertEqual(self.store.get(identity), before)
                self.assertEqual(self.runtime.contexts, [])

    def test_initial_enqueue_failure_can_be_discarded_without_inference(self):
        for fault in ('before', 'after'):
            with self.subTest(fault=fault):
                identity = self.create()
                self.store.queue_fault = fault
                with self.assertRaises(StorageUnavailable):
                    self.submit(identity)
                failed = self.engine.investigations.get(identity)['turns'][-1]
                discarded = self.engine.retry_storage(identity, discard=True)
                self.assertEqual([t['id'] for t in discarded['turns']], [failed['id']])
                self.assertEqual(discarded['turns'][-1]['status'], 'discarded')
                self.assertEqual(self.runtime.contexts, [])

    def test_dispatch_start_failure_is_retryable_without_phantom_worker(self):
        for target in ('slice.workflow.threading.Thread', 'slice.workflow.threading.Thread.start'):
            for failed_receipt in (False, True):
                with self.subTest(target=target, failed_receipt=failed_receipt):
                    identity = self.create()
                    request_id = str(time.time_ns())
                    calls = len(self.runtime.contexts)
                    if failed_receipt:
                        self.store.interrupted_fail.add(identity)
                    with patch(target, side_effect=RuntimeError("can't start new thread")):
                        with self.assertRaisesRegex(RuntimeError, "can't start new thread"):
                            self.engine.submit(identity, 'Samsung 2023 revenue', 'en', request_id)
                    self.assertEqual(self.engine.events, {})
                    self.assertFalse(self.engine.gate.locked())
                    failed = self.engine.investigations.get(identity)['turns'][-1]
                    self.assertEqual(failed['status'], 'storage_failed' if failed_receipt else 'interrupted')
                    self.assertEqual(len(self.runtime.contexts), calls)
                    repeated = self.engine.submit(identity, 'Samsung 2023 revenue', 'en', request_id)
                    self.assertEqual(repeated['id'], failed['id'])
                    if failed_receipt:
                        with self.assertRaises(StorageUnavailable):
                            self.engine.retry_storage(identity)
                        self.store.interrupted_fail.remove(identity)
                        restored = self.engine.retry_storage(identity)['turns'][-1]
                        self.assertEqual(restored['status'], 'interrupted')
                    self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                                       retry=failed['id'])
                    self.wait()
                    durable = self.store.get(identity)
                    self.assertEqual([t['status'] for t in durable['turns']], ['interrupted', 'complete'])
                    self.assertEqual(len(self.runtime.contexts), calls + 1)

    def test_completed_retry_does_not_reset_raw_diagnostic_retention(self):
        for diagnostics in (False, True):
            with self.subTest(diagnostics=diagnostics):
                identity = self.create()
                calls = len(self.runtime.contexts)
                self.store.receipt_fail.add(identity)
                self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                                   diagnostics=True)
                self.wait()
                self.store.receipt_fail.remove(identity)
                original = self.engine.retry_storage(identity)['turns'][-1]
                self.assertIn('content', original['model_record'])
                created_at = (datetime.now(timezone.utc) - timedelta(hours=23)).isoformat()
                self.store.change(identity, lambda body: body['turns'][-1].update(created_at=created_at))
                self.engine.submit(identity, 'Samsung 2023 revenue', 'en', str(time.time_ns()),
                                   retry=original['id'], diagnostics=diagnostics)
                self.wait()
                retry = self.store.get(identity)['turns'][-1]
                self.assertEqual(retry['status'], 'complete')
                self.assertEqual(retry['intent'], original['intent'])
                self.assertEqual(retry['model_record']['model'], original['model_record']['model'])
                self.assertTrue(retry['steps'][0]['reused'])
                self.assertEqual(len(self.runtime.contexts), calls + 1)
                with self.subTest(stage='completed retry'):
                    self.assertNotIn('content', retry['model_record'])
                created_at = (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
                self.store.change(identity, lambda body: body['turns'][0].update(created_at=created_at))
                Store().expire_diagnostics()
                durable = self.store.get(identity)
                self.assertNotIn('content', durable['turns'][0]['model_record'])
                with self.subTest(stage='original expired'):
                    self.assertNotIn('content', durable['turns'][-1]['model_record'])

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
