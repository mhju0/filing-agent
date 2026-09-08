"""Same-origin local application. Public replay uses separate static assets."""

import asyncio
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from slice.core import ROOT, SNAPSHOT
from slice.store import Store
from slice.workflow import Engine

ORIGIN = "http://127.0.0.1:8765"
TOKEN = secrets.token_urlsafe(32)
store = Store()
engine = Engine(store)


@asynccontextmanager
async def lifespan(app):
    store.setup()
    if store.recover():
        engine.runtime.blocked = True

    async def cleanup():
        while True:
            await asyncio.to_thread(store.expire_diagnostics)
            await asyncio.to_thread(store.history)
            await asyncio.sleep(60)

    cleanup_task = asyncio.create_task(cleanup())
    yield
    cleanup_task.cancel()
    engine.pool.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def local_boundary(request: Request, call_next):
    if request.headers.get("host") != "127.0.0.1:8765":
        return JSONResponse({"detail": "Loopback host required"}, status_code=403)
    if request.headers.get("origin") not in (None, ORIGIN):
        return JSONResponse({"detail": "Cross-origin request refused"}, status_code=403)
    if request.headers.get("sec-fetch-site") == "cross-site":
        return JSONResponse({"detail": "Cross-site request refused"}, status_code=403)
    if request.method not in ("GET", "HEAD"):
        if request.headers.get("x-filing-token") != TOKEN:
            return JSONResponse(
                {"detail": "Local session token required"}, status_code=403
            )
        if int(request.headers.get("content-length", "0")) > 8192:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(ValueError)
async def invalid(request, exc):
    return JSONResponse({"detail": str(exc)}, status_code=409)


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

    return {"token": TOKEN, "coverage": json.loads(SNAPSHOT.read_text())["coverage"]}


@app.get("/api/history")
def history():
    return store.history()


@app.post("/api/investigations")
def create():
    return store.create()


@app.get("/api/investigations/{identity}")
def investigation(identity: UUID):
    return store.get(str(identity))


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
    return store.save(str(identity))


@app.post("/api/investigations/{identity}/fork")
def fork(identity: UUID, body: Fork):
    return store.create(str(identity), body.mode)


@app.post("/api/turns/{identity}/cancel")
def cancel(identity: UUID):
    engine.cancel(str(identity))
    return {"status": "stop_requested"}


@app.post("/api/investigations/{identity}/delete")
def delete(identity: UUID):
    store.delete(str(identity))
    return {"status": "deleted"}


web = Path(ROOT / "slice/web/dist")
if web.exists():
    app.mount("/", StaticFiles(directory=web, html=True), name="web")
