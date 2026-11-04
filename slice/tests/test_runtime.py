import json
import threading
import unittest
from multiprocessing import get_context
from unittest.mock import Mock, call, patch

from slice.core import DIGEST, MODEL, OPTIONS
from slice.runtime import Runtime, Stopped


INTENT = {
    "companies": ["Samsung"],
    "metric": "revenue",
    "periods": ["2023"],
    "basis": "consolidated",
    "action": "report",
}
QUESTION = "Samsung 2023 revenue"
FAILURE = "Local inference failed; check the controlled Ollama server"


def exit_without_response(connection, payload, timeout):
    connection.close()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.runtime = Runtime()
        self.reader = Mock()
        self.writer = Mock()
        self.process = Mock()
        self.process.is_alive.return_value = False
        self.context = Mock()
        self.context.Pipe.return_value = self.reader, self.writer
        self.context.Process.return_value = self.process
        self.reader.poll.return_value = True
        self.reader.recv.return_value = {
            "response": {
                "done": True,
                "done_reason": "stop",
                "message": {"content": json.dumps(INTENT)},
                "eval_count": 20,
            }
        }
        self.cancel = threading.Event()
        self.api = Mock(side_effect=[{"done": True}, {"models": []}])
        self.events = Mock()
        self.events.attach_mock(self.process, "process")
        self.events.attach_mock(self.api, "api")
        for target, kwargs in [
            ("slice.runtime.multiprocessing.get_context", {"return_value": self.context}),
            ("slice.runtime.api", {"new": self.api}),
        ]:
            patcher = patch(target, **kwargs)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(self.runtime, "preflight")
        patcher.start()
        self.addCleanup(patcher.stop)

    def interpret(self):
        return self.runtime.interpret(QUESTION, None, self.cancel)

    def assert_client_closed(self):
        self.reader.close.assert_called()
        self.writer.close.assert_called()
        self.process.join.assert_called_with(1)

    def assert_stop_requested(self):
        self.assertEqual(self.api.call_args_list, [
            call("POST", "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=8),
            call("GET", "/api/ps", timeout=2),
        ])
        names = [event[0] for event in self.events.mock_calls]
        self.assertLess(names.index("process.join"), names.index("api"))

    def test_worker_eof_reaps_client_and_confirms_runtime_stop(self):
        self.reader.recv.side_effect = EOFError
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.assert_client_closed()
        self.assert_stop_requested()
        self.assertFalse(self.runtime.blocked)

    def test_spawned_worker_exit_without_response_blocks_unconfirmed_stop(self):
        context = get_context("spawn")
        self.context.Pipe.return_value = context.Pipe(duplex=False)
        processes = []

        def create_process(**kwargs):
            process = context.Process(**kwargs)
            processes.append(process)
            return process

        self.context.Process.side_effect = create_process
        self.api.side_effect = [{"done": True}, {"models": [{"name": MODEL}]}]
        with patch("slice.runtime.chat_worker", exit_without_response):
            with self.assertRaisesRegex(ValueError, FAILURE):
                self.interpret()
        self.assertEqual(len(processes), 1)
        self.assertFalse(processes[0].is_alive())
        self.assertTrue(all(end.closed for end in self.context.Pipe.return_value))
        self.assertEqual(self.api.call_count, 2)
        self.assertTrue(self.runtime.blocked)

    def test_receive_failure_blocks_when_runtime_is_still_loaded(self):
        self.reader.recv.side_effect = OSError("worker pipe failed")
        self.api.side_effect = [{"done": True}, {"models": [{"name": MODEL}]}]
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.assert_client_closed()
        self.assert_stop_requested()
        self.assertTrue(self.runtime.blocked)

    def test_poll_failure_blocks_when_stop_confirmation_is_unavailable(self):
        self.reader.poll.side_effect = OSError("worker pipe failed")
        self.api.side_effect = OSError("controlled runtime unavailable")
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.assert_client_closed()
        self.api.assert_called_once_with(
            "POST", "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=8
        )
        self.assertTrue(self.runtime.blocked)

    def test_surviving_client_blocks_next_call_despite_empty_runtime(self):
        self.process.is_alive.return_value = True
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.assertTrue(self.runtime.blocked)
        self.assert_stop_requested()
        self.process.kill.assert_called_once()
        self.api.reset_mock()
        self.api.side_effect = [
            {"version": "0.33.3"},
            {"models": [{"name": MODEL, "digest": DIGEST, "size": 1}]},
        ]
        with (
            patch.object(self.runtime, "preflight", wraps=lambda: Runtime.preflight(self.runtime)),
            patch("slice.runtime.Path.read_text", return_value='{"disable_ollama_cloud": true}'),
            patch("slice.runtime.local_model_info"),
        ):
            with self.assertRaisesRegex(ValueError, "Previous inference stop is unconfirmed"):
                self.interpret()
        self.process.start.assert_called_once()
        self.assertTrue(self.runtime.blocked)
        self.assertNotIn(call("GET", "/api/ps"), self.api.call_args_list)

    def test_reaped_client_requires_stop_confirmation_before_next_call(self):
        self.process.is_alive.return_value = True
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.process.is_alive.return_value = False
        self.api.reset_mock()
        self.api.side_effect = [
            {"version": "0.33.3"},
            {"models": [{"name": MODEL, "digest": DIGEST, "size": 1}]},
            {"done": True},
            {"models": []},
        ]
        with (
            patch.object(self.runtime, "preflight", wraps=lambda: Runtime.preflight(self.runtime)),
            patch("slice.runtime.Path.read_text", return_value='{"disable_ollama_cloud": true}'),
            patch("slice.runtime.local_model_info"),
        ):
            intent, _ = self.interpret()
        self.assertEqual(intent, INTENT)
        self.assertFalse(self.runtime.blocked)
        self.assertEqual(self.process.start.call_count, 2)
        self.assertEqual(self.api.call_args_list[-2:], [
            call("POST", "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=8),
            call("GET", "/api/ps", timeout=2),
        ])

    def test_start_failure_closes_pipes_without_stopping_unstarted_inference(self):
        self.process.start.side_effect = OSError("spawn failed")
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.reader.close.assert_called_once()
        self.writer.close.assert_called_once()
        self.process.join.assert_not_called()
        self.process.terminate.assert_not_called()
        self.api.assert_not_called()
        self.assertFalse(self.runtime.blocked)

    def test_process_creation_failure_closes_pipes_without_stopping_runtime(self):
        self.context.Process.side_effect = OSError("process unavailable")
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.reader.close.assert_called_once()
        self.writer.close.assert_called_once()
        self.api.assert_not_called()

    def test_cancel_kills_stubborn_client_before_stop_confirmation(self):
        self.cancel.set()
        self.process.is_alive.side_effect = [True, True, False]
        with self.assertRaises(Stopped) as caught:
            self.interpret()
        self.assertTrue(caught.exception.confirmed)
        self.assertFalse(caught.exception.timeout)
        self.assert_client_closed()
        self.process.terminate.assert_called_once()
        self.process.kill.assert_called_once()
        self.assert_stop_requested()
        self.reader.recv.assert_not_called()

    def test_timeout_retains_unconfirmed_stop_state(self):
        self.api.side_effect = [{"done": True}, {"models": [{"name": MODEL}]}]
        with patch("slice.runtime.time.monotonic", side_effect=[0, 120]):
            with self.assertRaises(Stopped) as caught:
                self.interpret()
        self.assertTrue(caught.exception.timeout)
        self.assertFalse(caught.exception.confirmed)
        self.assertTrue(self.runtime.blocked)
        self.assert_stop_requested()

    def test_worker_error_requests_runtime_stop(self):
        self.reader.recv.return_value = {"error": "request failed"}
        with self.assertRaisesRegex(ValueError, FAILURE):
            self.interpret()
        self.assert_stop_requested()

    def test_completed_response_preserves_pinned_payload_and_intent_metadata(self):
        intent, metadata = self.interpret()
        self.assertEqual(intent, INTENT)
        self.assertEqual(metadata["model"], MODEL)
        self.assertEqual(metadata["digest"], DIGEST)
        self.assertEqual(metadata["runtime"], "0.33.3")
        self.assertEqual(metadata["options"], OPTIONS)
        self.assertEqual(metadata["metrics"]["eval_count"], 20)
        payload = self.context.Process.call_args.kwargs["args"][1]
        self.assertEqual(payload["model"], MODEL)
        self.assertEqual(payload["options"], OPTIONS)
        self.assertFalse(payload["stream"])
        self.assertFalse(payload["think"])
        self.assert_client_closed()
        self.api.assert_not_called()

    def test_incomplete_response_is_never_accepted(self):
        for done, reason in [(False, "stop"), (True, "length")]:
            with self.subTest(done=done, reason=reason):
                body = self.reader.recv.return_value["response"]
                body.update(done=done, done_reason=reason)
                with self.assertRaisesRegex(ValueError, "Incomplete local interpretation"):
                    self.interpret()
        self.api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
