"""Explicit private backup and restore. Restores receive new investigation IDs."""

import argparse
import copy
import json
import os
from pathlib import Path

from psycopg.types.json import Jsonb

from slice.core import checksum, financial_answer, validate_snapshot
from slice.store import Store, now, uid


def backup(path):
    store = Store()
    investigations = store.history()
    if any(
        t["status"] in ("running", "queued") for i in investigations for t in i["turns"]
    ):
        raise ValueError("Finish or cancel running work before backup")
    for i in investigations:
        for t in i["turns"]:
            t.get("model_record", {}).pop("content", None)
    body = {
        "schema": "filing-agent-private-backup-v1",
        "created_at": now(),
        "investigations": investigations,
        "snapshots": [
            store.snapshot(s)
            for s in sorted({i["snapshot_id"] for i in investigations})
        ],
    }
    body["sha256"] = checksum(body)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2)
    return len(investigations)


def restore(path):
    store = Store()
    body = json.loads(path.read_text())
    expected = body.pop("sha256")
    if (
        body.get("schema") != "filing-agent-private-backup-v1"
        or checksum(body) != expected
    ):
        raise ValueError("Backup schema or checksum is invalid")
    snapshots = {s["snapshot_id"]: validate_snapshot(s) for s in body["snapshots"]}
    for inv in body["investigations"]:
        if inv["snapshot_id"] not in snapshots:
            raise ValueError("Backup lacks pinned evidence")
        facts = {f["id"]: f for f in snapshots[inv["snapshot_id"]]["facts"]}
        for turn in inv["turns"]:
            if turn["status"] in ("running", "queued"):
                raise ValueError("Cannot restore an active attempt")
            for figure in turn.get("answer", {}).get("figures", []):
                if facts.get(figure["id"]) != figure:
                    raise ValueError("Backup figure differs from pinned evidence")
            if "answer" in turn:
                expected_answer = financial_answer(
                    turn["intent"], snapshots[inv["snapshot_id"]], turn["question"]
                )
                # Historical wording and supported partial-result policy remain frozen.
                # Restored calculations must still match the evidence-bound arithmetic.
                if turn["answer"]["calculated"] != expected_answer["calculated"]:
                    raise ValueError("Backup calculation differs from pinned evidence")
    ids = []
    with store.connect() as db:
        for identity, snapshot in snapshots.items():
            db.execute(
                "INSERT INTO snapshots VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (identity, Jsonb(snapshot)),
            )
        for inv in body["investigations"]:
            new = copy.deepcopy(inv)
            new.update(
                id=uid(),
                touched_at=now(),
                lineage={"mode": "restore", "investigation_id": inv["id"]},
            )
            db.execute(
                "INSERT INTO investigations VALUES (%s,%s)", (new["id"], Jsonb(new))
            )
            ids.append(new["id"])
    return ids


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "restore", "clear-diagnostics"])
    parser.add_argument("file", nargs="?", type=Path)
    args = parser.parse_args()
    if args.action == "clear-diagnostics":
        Store().expire_diagnostics(immediate=True)
    elif not args.file:
        parser.error("File path required")
    elif args.action == "backup":
        print("Investigations backed up:", backup(args.file))
    else:
        print("Restored investigation IDs:", restore(args.file))
