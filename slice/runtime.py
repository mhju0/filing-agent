"""Pinned loopback inference with a killable client and explicit stop confirmation."""

import json
import multiprocessing
import time
from pathlib import Path

from slice.core import DIGEST, MODEL, OPTIONS, ROOT, SCHEMA, guard_intent, parse_intent

# The core establishes the measured benchmark module path before these imports.
# isort: split
from run import api, chat_worker, local_model_info


class Stopped(Exception):
    def __init__(self, confirmed, timeout=False):
        self.confirmed = confirmed
        self.timeout = timeout


class Runtime:
    def __init__(self):
        self.blocked = False

    def preflight(self):
        config = json.loads((Path.home() / ".ollama/server.json").read_text())
        if config.get("disable_ollama_cloud") is not True:
            raise ValueError("Ollama cloud must be disabled")
        if api("GET", "/api/version")["version"] != "0.33.3":
            raise ValueError("Ollama version changed; requalification required")
        model = next(
            (m for m in api("GET", "/api/tags")["models"] if m["name"] == MODEL), None
        )
        if not model or model.get("digest") != DIGEST or model.get("size", 0) <= 0:
            raise ValueError("Pinned local weights unavailable")
        local_model_info(MODEL)
        if self.blocked:
            if api("GET", "/api/ps").get("models"):
                raise ValueError(
                    "Previous inference stop is unconfirmed; restart the controlled Ollama server"
                )
            self.blocked = False

    def stop(self):
        self.blocked = True
        try:
            api("POST", "/api/generate", {"model": MODEL, "keep_alive": 0}, timeout=8)
            if not api("GET", "/api/ps", timeout=2).get("models"):
                self.blocked = False
                return True
        except Exception:  # noqa: BLE001 - any failed stop confirmation must block inference
            return False
        return False

    def interpret(self, question, context, cancel):
        started = time.monotonic()
        self.preflight()
        system = (
            (ROOT / "bench/prompts/intent.txt").read_text()
            + "\nSCHEMA: "
            + json.dumps(SCHEMA)
        )
        payload = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": system},
                {
                    "role": "user",
                    "content": "CONTEXT: "
                    + json.dumps(context, ensure_ascii=False)
                    + "\nQUESTION: "
                    + question,
                },
            ],
            "format": SCHEMA,
            "options": OPTIONS,
            "stream": False,
            "think": False,
            "keep_alive": "5m",
        }
        ctx = multiprocessing.get_context("spawn")
        reader, writer = ctx.Pipe(duplex=False)
        process = ctx.Process(
            target=chat_worker, args=(writer, payload, 120), daemon=True
        )
        process.start()
        writer.close()
        stopped = False
        timeout = False
        try:
            while True:
                timeout = time.monotonic() - started >= 120
                if cancel.is_set() or timeout:
                    stopped = True
                    break
                if reader.poll(0.05):
                    response = reader.recv()
                    break
        finally:
            reader.close()
            if process.is_alive():
                process.terminate()
            process.join(1)
            if process.is_alive():
                process.kill()
                process.join(1)
        if stopped:
            raise Stopped(self.stop(), timeout)
        if "error" in response:
            self.stop()
            raise ValueError(
                "Local inference failed; check the controlled Ollama server"
            )
        body = response["response"]
        if body.get("done") is not True or body.get("done_reason") == "length":
            raise ValueError("Incomplete local interpretation; no figures accepted")
        content = body["message"]["content"]
        intent = guard_intent(question, parse_intent(content), context)
        return intent, {
            "model": MODEL,
            "digest": DIGEST,
            "runtime": "0.33.3",
            "options": OPTIONS,
            "content": content,
            "wall_seconds": time.monotonic() - started,
            "metrics": {
                k: body.get(k) for k in ("load_duration", "eval_count", "eval_duration")
            },
        }
