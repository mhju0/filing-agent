"""Same-origin local application. Public replay uses separate static assets."""

import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID

import psycopg

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.datastructures import MutableHeaders
from starlette.requests import ClientDisconnect

from slice.core import ROOT, SNAPSHOT
from slice.store import Store
from slice.workflow import Engine

ORIGIN = "http://127.0.0.1:8765"
TOKEN = secrets.token_urlsafe(32)
store = Store()
engine = Engine(store)
investigations = engine.investigations


@asynccontextmanager
async def lifespan(app):
    store.setup()
    if store.recover():
        engine.runtime.blocked = True

    async def cleanup():
        while True:
            try:
                await asyncio.to_thread(store.expire_diagnostics)
                await asyncio.to_thread(store.history)
            except psycopg.Error:
                pass  # Resume retention cleanup after storage becomes available.
            await asyncio.sleep(60)

    cleanup_task = asyncio.create_task(cleanup())
    yield
    cleanup_task.cancel()
    engine.pool.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


class LocalBoundary:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        request = Request(scope, receive)

        async def secured_send(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["Content-Security-Policy"] = (
                    "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
                )
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Referrer-Policy"] = "no-referrer"
                headers["Cache-Control"] = "no-store"
            await send(message)

        async def reject(detail, status):
            await JSONResponse({"detail": detail}, status_code=status)(scope, receive, secured_send)

        if request.headers.get("host") != "127.0.0.1:8765":
            return await reject("Loopback host required", 403)
        if request.headers.get("origin") not in (None, ORIGIN):
            return await reject("Cross-origin request refused", 403)
        if request.headers.get("sec-fetch-site") == "cross-site":
            return await reject("Cross-site request refused", 403)
        if request.method not in ("GET", "HEAD"):
            if request.headers.get("x-filing-token") != TOKEN:
                return await reject("Local session token required", 403)
            lengths = request.headers.getlist("content-length")
            if lengths:
                if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdecimal():
                    return await reject("Invalid Content-Length", 400)
                length = lengths[0].lstrip("0")
                if len(length) > 4 or (len(length) == 4 and length > "8192"):
                    return await reject("Request too large", 413)
            body = bytearray()
            try:
                async for chunk in request.stream():
                    if len(body) + len(chunk) > 8192:
                        return await reject("Request too large", 413)
                    body.extend(chunk)
            except ClientDisconnect:
                return

            async def buffered_receive():
                nonlocal body
                if body is not None:
                    message = {"type": "http.request", "body": bytes(body), "more_body": False}
                    body = None
                    return message
                return await receive()

            return await self.app(scope, buffered_receive, secured_send)
        return await self.app(scope, receive, secured_send)


app.add_middleware(LocalBoundary)


@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=409)


@app.exception_handler(psycopg.Error)
async def storage_unavailable(request, exc):
    return JSONResponse({"detail": "Storage unavailable; check the local database and retry"}, status_code=503)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    language: Literal["ko", "en"]
    request_id: UUID
    retry_of: UUID | None = None
    diagnostics: bool = False


class Fork(BaseModel):
    mode: Literal["continue", "refresh"]


@app.get("/api/session")
def session():
    import json

    return {"token": TOKEN, "coverage": json.loads(SNAPSHOT.read_text())["coverage"], "running": engine.gate.locked()}


@app.get("/api/history")
def history():
    return investigations.history()


@app.post("/api/investigations")
def create():
    return investigations.create()


@app.get("/api/investigations/{identity}")
def investigation(identity: UUID):
    return investigations.get(str(identity))


@app.post("/api/investigations/{identity}/turns")
def question(identity: UUID, body: Question):
    if not body.question.strip():
        raise HTTPException(422, "Question is empty")
    return engine.submit(
        str(identity),
        body.question.strip(),
        body.language,
        str(body.request_id),
        str(body.retry_of) if body.retry_of else None,
        body.diagnostics,
    )


@app.post("/api/investigations/{identity}/save")
def save(identity: UUID):
    return investigations.save(str(identity))


@app.post("/api/investigations/{identity}/fork")
def fork(identity: UUID, body: Fork):
    return investigations.create(str(identity), body.mode)


@app.post("/api/turns/{identity}/cancel")
def cancel(identity: UUID):
    engine.cancel(str(identity))
    return {"status": "stop_requested"}


@app.post("/api/investigations/{identity}/delete")
def delete(identity: UUID):
    investigations.delete(str(identity))
    return {"status": "deleted"}


@app.post("/api/investigations/{identity}/retry-storage")
def retry_storage(identity: UUID):
    return engine.retry_storage(str(identity))


@app.post("/api/investigations/{identity}/discard-unstored")
def discard_unstored(identity: UUID):
    return engine.retry_storage(str(identity), discard=True)


web = Path(ROOT / "slice/web/dist")
if web.exists():
    app.mount("/", StaticFiles(directory=web, html=True), name="web")
