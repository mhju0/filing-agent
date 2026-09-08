"""Run full local API scenarios; retain raw outputs and per-trial language gates."""

import argparse
import hashlib
import json
import time
from pathlib import Path
from uuid import uuid4

import requests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=["dev", "heldout"], required=True)
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError(
            "Results are append-only experiments; select a new output path"
        )
    session = requests.Session()
    session.trust_env = False
    base = "http://127.0.0.1:8765/api"
    session.headers["X-Filing-Token"] = session.get(
        base + "/session", timeout=5
    ).json()["token"]

    def api(path, body=None):
        response = (
            session.get(base + path, timeout=10)
            if body is None
            else session.post(base + path, json=body, timeout=10)
        )
        response.raise_for_status()
        return response.json()

    all_cases = json.loads(Path("evals/cases.json").read_text())
    cases = [c for c in all_cases if c["split"] == args.split]
    result = {
        "status": "running",
        "split": args.split,
        "trials": args.trials,
        "case_sha256": hashlib.sha256(
            Path("evals/cases.json").read_bytes()
        ).hexdigest(),
        "runs": [],
        "source_sha256": {
            str(p): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in Path("slice").glob("*.py")
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)

    def save():
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    for trial in range(args.trials):
        for case in cases:
            inv = api("/investigations", {})
            entry = {
                "case": case["id"],
                "language": case["language"],
                "trial": trial + 1,
                "turns": [],
                "pass": False,
            }
            for step in case["turns"]:
                turn = api(
                    "/investigations/" + inv["id"] + "/turns",
                    {
                        "question": step["question"],
                        "language": case["language"],
                        "request_id": str(uuid4()),
                        "diagnostics": True,
                    },
                )
                deadline = time.monotonic() + 145
                while time.monotonic() < deadline:
                    inv = api("/investigations/" + inv["id"])
                    current = next(t for t in inv["turns"] if t["id"] == turn["id"])
                    if (
                        current["status"] not in ("running", "queued")
                        and "wall_seconds" in current
                    ):
                        break
                    time.sleep(0.1)
                else:
                    raise TimeoutError("Application evaluation deadline")
                entry["turns"].append(current)
            answer = current.get("answer", {})
            expected = case["turns"][-1]["expected"]
            actual = {
                k: sorted(answer.get(k, []))
                if k in ("companies", "periods")
                else answer.get(k)
                for k in expected
                if k != "figures"
            }
            actual["figures"] = {f["id"]: f["value"] for f in answer.get("figures", [])}
            entry.update(expected=expected, actual=actual)
            entry["pass"] = current["status"] == "complete" and actual == expected
            if answer.get("calculated"):
                from decimal import ROUND_HALF_UP, Decimal

                prior, latest = sorted(answer["figures"], key=lambda f: f["period"])
                delta = Decimal(latest["value"]) - Decimal(prior["value"])
                percent = (delta / Decimal(prior["value"]) * 100).quantize(
                    Decimal(".01"), rounding=ROUND_HALF_UP
                )
                entry["pass"] &= answer["calculated"][0]["percentage_change"] == str(
                    percent
                )
            result["runs"].append(entry)
            save()
            print(
                f"{args.split} {trial + 1}/{args.trials} {len(result['runs'])}: {case['id']} {'PASS' if entry['pass'] else 'FAIL'}",
                flush=True,
            )
            api("/investigations/" + inv["id"] + "/delete", {})
    result["status"] = "complete"
    result["scores"] = [
        {
            "language": lang,
            "trial": trial,
            "correct": sum(
                r["pass"]
                for r in result["runs"]
                if r["language"] == lang and r["trial"] == trial
            ),
            "total": sum(
                r["language"] == lang and r["trial"] == trial for r in result["runs"]
            ),
        }
        for trial in range(1, args.trials + 1)
        for lang in ("ko", "en")
    ]
    result["gate_pass"] = all(
        row["correct"] / row["total"] >= 0.95 for row in result["scores"]
    )
    save()
    print(result["scores"], flush=True)


if __name__ == "__main__":
    main()
