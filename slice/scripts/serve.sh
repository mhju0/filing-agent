#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
export LANGSMITH_TRACING=false LANGCHAIN_TRACING_V2=false LANGSMITH_OTEL_ENABLED=false
unset LANGSMITH_API_KEY LANGCHAIN_API_KEY
exec .venv/bin/python -m uvicorn slice.app:app --host 127.0.0.1 --port 8765 --workers 1 --no-access-log
