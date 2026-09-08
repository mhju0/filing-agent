#!/bin/sh
set -eu
cd "$(dirname "$0")/../.."
./slice/scripts/database.sh
printf '%s\n' 'Start ./bench/serve.sh in a separate terminal, then open http://127.0.0.1:8765'
exec ./slice/scripts/serve.sh
