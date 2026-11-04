import asyncio
import json
import unittest
from unittest.mock import patch
from uuid import uuid4

from slice import app as local


class HttpBoundaryTests(unittest.IsolatedAsyncioTestCase):
    async def request(self, chunks=(), headers=(), method="POST", path=None):
        identity = str(uuid4())
        messages = []
        reads = 0
        body_chunks = iter(chunks)
        scope = {
            "type": "http", "asgi": {"version": "3.0"},
            "http_version": "1.1", "method": method, "scheme": "http",
            "path": path or f"/api/investigations/{identity}/turns",
            "raw_path": b"/", "query_string": b"", "root_path": "",
            "server": ("127.0.0.1", 8765), "client": ("127.0.0.1", 12345),
            "headers": list(headers),
        }

        async def receive():
            nonlocal reads
            try:
                chunk, more = next(body_chunks)
            except StopIteration:
                await asyncio.Event().wait()
            reads += 1
            return {"type": "http.request", "body": chunk, "more_body": more}

        async def send(message):
            messages.append(message)

        with patch.object(local.engine, "submit", return_value={"status": "queued"}) as submit:
            await asyncio.wait_for(local.app(scope, receive, send), timeout=2)
        start = next(message for message in messages if message["type"] == "http.response.start")
        body = b"".join(message.get("body", b"") for message in messages
                        if message["type"] == "http.response.body")
        return start["status"], json.loads(body), reads, submit, dict(start["headers"])

    def authorized(self, *extra):
        return [(b"host", b"127.0.0.1:8765"),
                (b"origin", local.ORIGIN.encode()),
                (b"x-filing-token", local.TOKEN.encode()),
                (b"content-type", b"application/json"), *extra]

    async def test_valid_stream_reaches_question_parser_with_or_without_length(self):
        request_id = str(uuid4())
        body = json.dumps({"question": "삼성전자 2023 매출액", "language": "ko",
                           "request_id": request_id}, ensure_ascii=False).encode()
        for extra in ((), ((b"content-length", str(len(body)).encode()),),
                      ((b"transfer-encoding", b"chunked"),)):
            with self.subTest(headers=extra):
                status, result, reads, submit, headers = await self.request(
                    [(body[:17], True), (body[17:], False)], self.authorized(*extra))
                self.assertEqual(status, 200)
                self.assertEqual(result, {"status": "queued"})
                self.assertEqual(reads, 2)
                self.assertEqual(submit.call_args.args[1:4],
                                 ("삼성전자 2023 매출액", "ko", request_id))
                self.assertEqual(headers[b"cache-control"], b"no-store")
                self.assertIn(b"frame-ancestors 'none'", headers[b"content-security-policy"])

    async def test_malformed_lengths_are_rejected_without_reading(self):
        for length in (b"", b"-1", b"+1", b"1.0", b"invalid", b" 1", b"1 ", b"\xb2", b"1, 1"):
            with self.subTest(length=length):
                status, _, reads, submit, _ = await self.request(
                    headers=self.authorized((b"content-length", length)))
                self.assertEqual(status, 400)
                self.assertEqual(reads, 0)
                submit.assert_not_called()
        status, _, reads, submit, _ = await self.request(headers=self.authorized(
            (b"content-length", b"1"), (b"content-length", b"2")))
        self.assertEqual(status, 400)
        self.assertEqual(reads, 0)
        submit.assert_not_called()

    async def test_declared_oversize_is_rejected_without_reading(self):
        for length in (b"8193", b"9" * 5000):
            with self.subTest(length=length[:20]):
                status, _, reads, submit, _ = await self.request(
                    headers=self.authorized((b"content-length", length)))
                self.assertEqual(status, 413)
                self.assertEqual(reads, 0)
                submit.assert_not_called()

    async def test_stream_limit_stops_before_remaining_chunks(self):
        for extra in ((), ((b"transfer-encoding", b"chunked"),),
                      ((b"content-length", b"1"),)):
            with self.subTest(headers=extra):
                status, result, reads, submit, _ = await self.request(
                    [(b"x" * 8192, True), (b"x", True), (b"never read", False)],
                    self.authorized(*extra))
                self.assertEqual(status, 413)
                self.assertEqual(result, {"detail": "Request too large"})
                self.assertEqual(reads, 2)
                submit.assert_not_called()

    async def test_single_oversize_chunk_is_rejected_before_route(self):
        status, _, reads, submit, _ = await self.request(
            [(b"x" * 65536, True), (b"never read", False)], self.authorized())
        self.assertEqual(status, 413)
        self.assertEqual(reads, 1)
        submit.assert_not_called()

    async def test_exact_limit_and_zero_padded_length_are_accepted(self):
        body = json.dumps({"question": "Samsung 2023 revenue", "language": "en",
                           "request_id": str(uuid4())}).encode().ljust(8192)
        status, _, reads, submit, _ = await self.request(
            [(body, False)], self.authorized((b"content-length", b"0" * 5000 + b"8192")))
        self.assertEqual(status, 200)
        self.assertEqual(reads, 1)
        submit.assert_called_once()

    async def test_security_rejections_do_not_read_body(self):
        for field, value in ((b"host", b"localhost:8765"),
                             (b"host", None),
                             (b"origin", b"https://example.com"),
                             (b"sec-fetch-site", b"cross-site"),
                             (b"x-filing-token", b"wrong"),
                             (b"x-filing-token", None)):
            with self.subTest(field=field, value=value):
                headers = [(key, existing) for key, existing in self.authorized() if key != field]
                if value is not None:
                    headers.append((field, value))
                headers.append((b"content-length", b"invalid"))
                status, _, reads, submit, response_headers = await self.request(headers=headers)
                self.assertEqual(status, 403)
                self.assertEqual(reads, 0)
                submit.assert_not_called()
                self.assertEqual(response_headers[b"cache-control"], b"no-store")
                self.assertEqual(response_headers[b"x-content-type-options"], b"nosniff")

    async def test_bodyless_mutation_reaches_existing_route(self):
        for extra in ((), ((b"content-length", b"0"),)):
            with self.subTest(headers=extra):
                with patch.object(local.investigations, "create", return_value={"id": "created"}) as create:
                    status, result, reads, _, _ = await self.request(
                        [(b"", False)], self.authorized(*extra), path="/api/investigations")
                self.assertEqual(status, 200)
                self.assertEqual(result, {"id": "created"})
                self.assertEqual(reads, 1)
                create.assert_called_once_with()

    async def test_disconnect_during_body_never_reaches_route(self):
        messages = iter([{"type": "http.request", "body": b"partial", "more_body": True},
                         {"type": "http.disconnect"}])
        sent = []
        reached = []

        async def receive():
            return next(messages)

        async def send(message):
            sent.append(message)

        async def downstream(scope, receive, send):
            reached.append(scope)

        await local.LocalBoundary(downstream)(
            {"type": "http", "method": "POST", "headers": self.authorized()}, receive, send)
        self.assertEqual(reached, [])
        self.assertEqual(sent, [])

    async def test_non_http_scope_passes_through(self):
        seen = []

        async def downstream(scope, receive, send):
            seen.append(scope)

        scope = {"type": "lifespan"}
        await local.LocalBoundary(downstream)(scope, None, None)
        self.assertEqual(seen, [scope])

    async def test_session_remains_accessible_without_mutation_token(self):
        status, result, reads, submit, _ = await self.request(
            headers=[(b"host", b"127.0.0.1:8765")], method="GET", path="/api/session")
        self.assertEqual(status, 200)
        self.assertEqual(result["token"], local.TOKEN)
        self.assertEqual(reads, 0)
        submit.assert_not_called()
