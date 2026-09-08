"""Agent-only PostgreSQL storage; transactions serialize conversation mutations."""

import copy
import json
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
from psycopg.types.json import Jsonb

from slice.core import SNAPSHOT
from slice.financial import validate_snapshot

BLOCKING = ("running", "queued", "saving", "storage_failed")

DSN = "host=127.0.0.1 port=55439 dbname=filing_agent_slice user=filing_agent connect_timeout=3"


def now():
    return datetime.now(timezone.utc).isoformat()


def uid():
    return str(uuid.uuid4())


class Store:
    def __init__(self, dsn=DSN):
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn)

    def setup(self):
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS snapshots (id text PRIMARY KEY, body jsonb NOT NULL)"
            )
            db.execute(
                "CREATE TABLE IF NOT EXISTS investigations (id uuid PRIMARY KEY, body jsonb NOT NULL)"
            )
        self.install(json.loads(SNAPSHOT.read_text()))

    def install(self, snapshot):
        validate_snapshot(snapshot)
        with self.connect() as db:
            db.execute(
                "INSERT INTO snapshots VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (snapshot["snapshot_id"], Jsonb(snapshot)),
            )
        if self.snapshot(snapshot["snapshot_id"]) != snapshot:
            raise ValueError("Snapshot identity collision")

    def snapshot(self, identity):
        with self.connect() as db:
            row = db.execute(
                "SELECT body FROM snapshots WHERE id=%s", (identity,)
            ).fetchone()
        if not row:
            raise ValueError("Pinned evidence unavailable; no substitution permitted")
        return validate_snapshot(row[0])

    def create(self, parent=None, mode=None):
        latest = json.loads(SNAPSHOT.read_text())["snapshot_id"]
        data = {
            "id": uid(),
            "created_at": now(),
            "touched_at": now(),
            "saved": False,
            "snapshot_id": latest,
            "accepted": None,
            "pending": None,
            "turns": [],
            "lineage": None,
        }
        if parent:
            old = self.get(parent)
            if any(t["status"] in BLOCKING for t in old["turns"]):
                raise ValueError("Wait for the current turn before forking")
            data["lineage"] = {"investigation_id": parent, "mode": mode}
            data["accepted"] = copy.deepcopy(old["accepted"])
            if mode == "continue":
                data["snapshot_id"] = old["snapshot_id"]
                data["pending"] = copy.deepcopy(old["pending"])
                data["turns"] = copy.deepcopy(old["turns"])
            elif mode != "refresh":
                raise ValueError("Unknown fork mode")
        self.snapshot(data["snapshot_id"])
        with self.connect() as db:
            db.execute(
                "INSERT INTO investigations VALUES (%s,%s)", (data["id"], Jsonb(data))
            )
        return data

    def get(self, identity):
        uuid.UUID(identity)
        with self.connect() as db:
            row = db.execute(
                "SELECT body FROM investigations WHERE id=%s", (identity,)
            ).fetchone()
        if not row:
            raise ValueError("Investigation unavailable")
        body = row[0]
        if not body["saved"] and datetime.fromisoformat(
            body["touched_at"]
        ) < datetime.now(timezone.utc) - timedelta(days=30):
            self.delete(identity)
            raise ValueError("Investigation expired after 30 idle days")
        return body

    def change(self, identity, fn):
        self.get(identity)
        with self.connect() as db:
            row = db.execute(
                "SELECT body FROM investigations WHERE id=%s FOR UPDATE", (identity,)
            ).fetchone()
            if not row:
                raise ValueError("Investigation unavailable")
            body = row[0]
            fn(body)
            body["touched_at"] = now()
            db.execute(
                "UPDATE investigations SET body=%s WHERE id=%s", (Jsonb(body), identity)
            )
        return body

    def history(self):
        with self.connect() as db:
            expired = db.execute(
                "SELECT id FROM investigations WHERE body->>'saved'='false' AND (body->>'touched_at')::timestamptz < now()-interval '30 days'"
            ).fetchall()
        for (identity,) in expired:
            self.delete(str(identity))
        with self.connect() as db:
            rows = db.execute(
                "SELECT body FROM investigations ORDER BY body->>'touched_at' DESC"
            ).fetchall()
        return [r[0] for r in rows]

    def save(self, identity):
        def freeze(body):
            if any(t["status"] in BLOCKING for t in body["turns"]):
                raise ValueError("Wait for completion before saving")
            body["saved"] = True

        return self.change(identity, freeze)

    def recover(self):
        recovered = False
        for data in self.history():
            if any(t["status"] in BLOCKING for t in data["turns"]):

                def mark(body):
                    for t in body["turns"]:
                        if t["status"] in BLOCKING:
                            t.update(
                                status="interrupted",
                                error="Application stopped; retry the interrupted step explicitly.",
                            )
                            for s in t["steps"]:
                                if s["status"] == "running":
                                    s["status"] = "interrupted"

                self.change(data["id"], mark)
                recovered = True
        return recovered

    def delete(self, identity):
        with self.connect() as db:
            row = db.execute(
                "SELECT body FROM investigations WHERE id=%s FOR UPDATE", (identity,)
            ).fetchone()
            if row and any(
                t["status"] in BLOCKING for t in row[0]["turns"]
            ):
                raise ValueError(
                    "Cancel and wait before deleting a running investigation"
                )
            db.execute("DELETE FROM investigations WHERE id=%s", (identity,))
            if db.execute("SELECT to_regclass('checkpoints')").fetchone()[0]:
                for table in ("checkpoints", "checkpoint_blobs", "checkpoint_writes"):
                    from psycopg import sql

                    db.execute(
                        sql.SQL("DELETE FROM {} WHERE thread_id=%s").format(
                            sql.Identifier(table)
                        ),
                        (identity,),
                    )

    def expire_diagnostics(self, immediate=False):
        threshold = datetime.now(timezone.utc) - timedelta(hours=24)
        with self.connect() as db:
            for identity, body in db.execute(
                "SELECT id, body FROM investigations FOR UPDATE"
            ).fetchall():
                changed = False
                for turn in body["turns"]:
                    if "content" in turn.get("model_record", {}) and (
                        immediate
                        or datetime.fromisoformat(turn["created_at"]) < threshold
                    ):
                        turn["model_record"].pop("content")
                        changed = True
                if changed:
                    db.execute(
                        "UPDATE investigations SET body=%s WHERE id=%s",
                        (Jsonb(body), identity),
                    )
