#!/bin/sh
# Gate: runs the same checks as the PR CI (.github/workflows/publication.yml).
# Usage: scripts/check.sh [--fast] [--part publication|application]
# --fast skips what needs PostgreSQL or a build: slice/tests and the web build.
# Dependencies (pip install -r slice/requirements.lock, npm ci in slice/web) are set up by CI, not here.
set -eu
cd "$(dirname "$0")/.."

FAST=""
PART="all"
while [ $# -gt 0 ]; do
  case "$1" in
    --fast) FAST=1 ;;
    --part) shift; PART="${1:-}" ;;
    *) echo "Usage: $0 [--fast] [--part publication|application]" >&2; exit 2 ;;
  esac
  shift
done
case "$PART" in all|publication|application) ;; *) echo "Unknown part: $PART" >&2; exit 2 ;; esac

PYTHON="${PYTHON:-python3}"
trap 'rc=$?; [ "$rc" -eq 0 ] || echo "GATE: FAIL"' EXIT

if [ "$PART" = all ] || [ "$PART" = publication ]; then
  "$PYTHON" release/check_publication.py
  "$PYTHON" -m unittest discover -s release/tests -v
fi

if [ "$PART" = all ] || [ "$PART" = application ]; then
  "$PYTHON" -m unittest discover -s bench/tests -v
  if [ -n "$FAST" ]; then
    (cd slice/web && npm test)
  else
    # slice/store.py connects to a fixed DSN (127.0.0.1:55439, db filing_agent_slice).
    # CI starts that service container; locally it must be a disposable server, never a personal one.
    if [ -z "${CI:-}" ] && [ -z "${SLICE_DB_OK:-}" ]; then
      echo "slice/tests need a disposable PostgreSQL on 127.0.0.1:55439 (db filing_agent_slice). Set SLICE_DB_OK=1 to confirm it is (CI sets CI=true), or use --fast." >&2
      exit 1
    fi
    "$PYTHON" -m unittest discover -s slice/tests -v
    (cd slice/web && npm test && npm run build)
  fi
fi

echo "GATE: PASS"
