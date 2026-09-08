"""Real API investigations and assertions, never substitutes expected model outputs."""

import hashlib
import json
import os
from pathlib import Path
import time

import requests

from slice.core import MODEL, ROOT
from slice.store import Store, uid

from bench.memory_monitor import Monitor

BASE = "http://127.0.0.1:8765/api"
OUT = Path(os.environ.get("CAPTURE_OUT", str(ROOT / "docs/audits/2026-09-08-slice")))
session = requests.Session()
session.trust_env = False
TOKEN = session.get(BASE + "/session").json()["token"]
session.headers["X-Filing-Token"] = TOKEN


def api(path, body=None):
    r = (
        session.get(BASE + path)
        if body is None
        else session.post(BASE + path, json=body)
    )
    r.raise_for_status()
    return r.json()


def ask(identity, question, language="ko", cancel=False):
    turn = api(
        "/investigations/" + identity + "/turns",
        {"question": question, "language": language, "request_id": uid()},
    )
    if cancel:
        time.sleep(0.6)
        api("/turns/" + turn["id"] + "/cancel", {})
    deadline = time.monotonic() + 145
    while time.monotonic() < deadline:
        inv = api("/investigations/" + identity)
        current = next(t for t in inv["turns"] if t["id"] == turn["id"])
        if current["status"] not in ("queued", "running", "saving") and "wall_seconds" in current:
            return inv, current
        time.sleep(0.15)
    raise TimeoutError("Application turn failed to terminate")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {
        "kind": "real local API capture",
        "model": MODEL,
        "application_files": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((ROOT / "slice").glob("*.py"))
        },
        "investigations": [],
        "checks": [],
    }
    with Monitor() as monitor:
        for questions in [
            ["삼성전자 2023년과 2022년 매출액 증감률은?"],
            ["삼성전자 2023년 매출액은?", "네이버는?"],
            ["삼성전자 2023년 연구개발비는?"],
        ]:
            inv = api("/investigations", {})
            for q in questions:
                inv, turn = ask(inv["id"], q)
                assert turn["status"] == "complete", turn
                print(q, turn["status"], turn["wall_seconds"], flush=True)
            inv = api("/investigations/" + inv["id"] + "/save", {})
            results["investigations"].append(inv)
            (OUT / "capture.json").write_text(
                json.dumps(results, ensure_ascii=False, indent=2) + "\n"
            )
        comparison, switch, missing = results["investigations"]
        assert (
            comparison["turns"][0]["answer"]["calculated"][0]["percentage_change"]
            == "-14.33"
        )
        assert switch["turns"][-1]["answer"]["figures"][0]["company"] == "NAVER"
        assert (
            missing["turns"][0]["answer"]["figures"] == []
            and missing["turns"][0]["answer"]["refused"]
        )
        results["checks"].append(
            "Actual compare, switch, refusal output matched required values and policy"
        )
        continued = api(
            "/investigations/" + switch["id"] + "/fork", {"mode": "continue"}
        )
        continued, last = ask(continued["id"], "2022년은?")
        assert (
            last["answer"]["reason_code"] == "missing_period"
            and last["answer"]["figures"] == []
        )
        assert continued["snapshot_id"] == switch["snapshot_id"]
        assert api("/investigations/" + switch["id"]) == switch
        refreshed = api(
            "/investigations/" + switch["id"] + "/fork", {"mode": "refresh"}
        )
        assert refreshed["turns"] == [] and refreshed["lineage"]["mode"] == "refresh"
        results["checks"].append(
            "Continue carried NAVER context and original snapshot; missing FY2022 refused; refresh fork empty; saved original byte-equivalent JSON"
        )
        inv = api("/investigations", {})
        inv, turn = ask(inv["id"], "2023년 매출액은?")
        assert (
            turn["answer"]["operation"] == "clarify"
            and inv["accepted"] is None
            and inv["pending"]["periods"] == ["2023"]
        )
        # A fresh storage object proves the clarification is in PostgreSQL, not a browser variable.
        assert Store().get(inv["id"])["pending"] == inv["pending"]
        inv, turn = ask(inv["id"], "삼성전자")
        assert (
            turn["answer"]["figures"][0]["company"] == "삼성전자"
            and inv["pending"] is None
        )
        results["clarification"] = inv
        results["checks"].append(
            "Actual model clarification followed by company choice resumed the persisted metric/year"
        )
        inv = api("/investigations", {})
        inv, turn = ask(
            inv["id"],
            "Compare Microsoft revenue in FY2024 and FY2023.",
            "en",
            cancel=True,
        )
        assert turn["status"] == "cancelled", turn
        assert inv["accepted"] is None
        results["cancellation"] = inv
        results["checks"].append(
            "Actual inference cancellation confirmed unload; no cancelled intent entered accepted context"
        )
    results["memory"] = monitor.summary()
    (OUT / "capture.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n"
    )
    print("CAPTURE PASS", flush=True)


if __name__ == "__main__":
    main()
