"""Capture Digest metadata in one read-only transaction without loading its app."""

import datetime as dt
import decimal
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

from dotenv import dotenv_values
import psycopg
from psycopg.rows import dict_row

HERE = Path(__file__).resolve().parent
DIGEST = HERE.parents[3] / "filing-digest"


def encode(value):
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, (decimal.Decimal, uuid.UUID)):
        return str(value)
    raise TypeError(type(value).__name__)


def canonical(value):
    return json.dumps(value, default=encode, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode()


def git(*args):
    return subprocess.check_output(["git", "-C", str(DIGEST), *args], text=True).strip()


def main():
    config = dotenv_values(DIGEST / "backend/.env")
    dsn = (config.get("DATABASE_URL") or "").replace("postgresql+psycopg://", "postgresql://")
    if not dsn:
        raise SystemExit("Missing database configuration; no connection attempted")
    before = git("status", "--porcelain")
    revision = git("rev-parse", "HEAD")
    with psycopg.connect(dsn, connect_timeout=5, row_factory=dict_row,
                         options="-c default_transaction_read_only=on -c statement_timeout=10000") as con:
        con.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        transaction = con.execute("SELECT current_setting('transaction_read_only') AS read_only, "
                                  "current_setting('transaction_isolation') AS isolation, "
                                  "version() AS server").fetchone()
        assert transaction["read_only"] == "on"
        companies = con.execute("SELECT * FROM companies ORDER BY id").fetchall()
        filings = con.execute("SELECT * FROM filings ORDER BY id").fetchall()
        facts = con.execute("SELECT * FROM financials ORDER BY id").fetchall()
        chunks = con.execute("SELECT id, filing_id, chunk_index, content, meta, "
                             "embedding IS NOT NULL AS embedded FROM filing_chunks "
                             "ORDER BY filing_id, chunk_index").fetchall()
        con.rollback()
    for chunk in chunks:
        content = chunk.pop("content")
        chunk["content_sha256"] = hashlib.sha256(content.encode()).hexdigest()
        chunk["characters"] = len(content)
    data = {"companies": companies, "filings": filings, "facts": facts, "chunks": chunks}
    manifest = {
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "upstream_revision": revision,
        "upstream_branch": git("branch", "--show-current"),
        "upstream_status_before": before,
        "upstream_status_after": git("status", "--porcelain"),
        "transaction": transaction,
        "corpus_sha256": hashlib.sha256(canonical(data)).hexdigest(),
        "fingerprint_scope": "All company/filing/fact columns; chunk identities, metadata and content hashes. Embedding values excluded.",
        "counts": {key: len(value) for key, value in data.items()},
        "schema_sha256": hashlib.sha256((DIGEST / "backend/db/init.sql").read_bytes()).hexdigest(),
        "vocabulary": json.loads((DIGEST / "contracts/financial-vocabulary.json").read_text()),
        "data": data,
    }
    assert manifest["upstream_status_after"] == before
    (HERE / "corpus.json").write_text(json.dumps(manifest, default=encode, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"counts": manifest["counts"], "corpus_sha256": manifest["corpus_sha256"]}))


if __name__ == "__main__":
    try:
        main()
    except psycopg.Error as error:
        raise SystemExit(f"Database export failed: {type(error).__name__}; connection details withheld") from None
