#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
TASK_DB="$PWD/.local/slice-postgres"
mkdir -p .local
if [ ! -f "$TASK_DB/PG_VERSION" ]; then
  initdb -D "$TASK_DB" -U filing_agent --auth-local=trust --auth-host=trust > .local/slice-initdb.log
  cat >> "$TASK_DB/postgresql.conf" <<CONFIG
listen_addresses = '127.0.0.1'
port = 55439
unix_socket_directories = ''
shared_buffers = '64MB'
max_connections = 20
CONFIG
fi
if ! pg_ctl -D "$TASK_DB" status >/dev/null 2>&1; then
  pg_ctl -D "$TASK_DB" -l "$PWD/.local/slice-postgres.log" start
fi
if [ "$(psql -h 127.0.0.1 -p 55439 -U filing_agent -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='filing_agent_slice'")" != "1" ]; then
  createdb -h 127.0.0.1 -p 55439 -U filing_agent filing_agent_slice
fi
