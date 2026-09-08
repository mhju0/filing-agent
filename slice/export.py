"""Export only explicitly selected completed investigations into a static bundle."""

import argparse
import copy
import json
import shutil
from pathlib import Path

from slice.core import ROOT, checksum
from slice.store import Store, now


def recording(investigations):
    translations = {
        "삼성전자 2023년과 2022년 매출액 증감률은?": "How did Samsung revenue change from FY2022 to FY2023?",
        "삼성전자 2023년 매출액은?": "What was Samsung revenue in FY2023?",
        "네이버는?": "What about NAVER?",
        "삼성전자 2023년 연구개발비는?": "What were Samsung R&D expenses in FY2023?",
    }
    output = []
    source_keys = (
        "regulator",
        "filing_title",
        "filing_identity",
        "url",
        "section",
        "link_status",
        "excerpt_cells",
        "excerpt",
    )
    for original in investigations:
        if (
            not original["saved"]
            or not original["turns"]
            or any(t["status"] != "complete" for t in original["turns"])
        ):
            raise ValueError("Replay export requires saved, completed investigations")
        inv = {
            k: copy.deepcopy(original[k])
            for k in ("id", "snapshot_id", "saved", "created_at")
        }
        inv.update(accepted=None, pending=None, lineage=None, turns=[])
        for turn in original["turns"]:
            if not turn.get("model_record") or not turn.get("wall_seconds"):
                raise ValueError("Replay requires actual captured execution and timing")
            item = {
                k: copy.deepcopy(turn[k])
                for k in (
                    "id",
                    "question",
                    "language",
                    "status",
                    "created_at",
                    "wall_seconds",
                    "answer",
                    "steps",
                )
            }
            for f in item["answer"]["figures"]:
                f["source"] = {
                    k: f["source"][k] for k in source_keys if k in f["source"]
                }
                f.pop("digest_fact_ids", None)
            if turn["question"] in translations:
                item["question_en"] = translations[turn["question"]]
            inv["turns"].append(item)
        output.append(inv)
    body = {
        "schema": "filing-agent-recording-v1",
        "recorded_at": now(),
        "investigations": output,
        "notice": "Authentic local execution; bilingual financial wording is supplied by code. Recorded against a fixed historical evidence collection; scope and evaluation limitations are documented in the accompanying project notes.",
    }
    body["sha256"] = checksum(body)
    return body


def export(ids, destination):
    store = Store()
    for identity in ids:
        store.snapshot(store.get(identity)["snapshot_id"])
    body = recording([store.get(i) for i in ids])
    destination = destination.resolve()
    if not destination.is_relative_to(ROOT / "slice") or destination.exists():
        raise ValueError("Use a new output directory inside slice")
    shutil.copytree(ROOT / "slice/web/dist", destination)
    # Replay is a separate entry point so it cannot accidentally bootstrap the live app.
    html = (
        (destination / "index.html")
        .read_text()
        .replace('<html lang="ko">', '<html lang="ko" data-mode="replay">')
    )
    html = html.replace(
        "<head>",
        "<head><meta http-equiv=\"Content-Security-Policy\" content=\"default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; form-action 'none'\"/>",
    )
    (destination / "index.html").write_text(html)
    (destination / "recording.json").write_text(
        json.dumps(body, ensure_ascii=False, indent=2) + "\n"
    )
    return body


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="+")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(export(args.ids, args.output)["sha256"])
