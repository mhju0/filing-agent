#!/bin/sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
TASK_RELEASE="$TASK_ROOT/slice/replay-release"
python3 - "$TASK_ROOT" "$TASK_RELEASE" <<'PY'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);out=Path(sys.argv[2])
report=json.loads((root/'docs/audits/2026-09-08-slice/artifact.json').read_text())
assert report['status']=='PASS' and (root/report['path']).resolve()==out.resolve()
actual={str(p.relative_to(out)) for p in out.rglob('*') if p.is_file() and '.vercel' not in p.parts}
assert actual==set(report['files']), 'Unexpected or missing release files'
for name,digest in report['files'].items():
 assert hashlib.sha256((out/name).read_bytes()).hexdigest()==digest,name
assert 'data-mode="replay"' in (out/'index.html').read_text()
assert not (out/'.git').exists()
print('Reviewed static artifact verified; deployment directory:',out)
PY
cd "$TASK_RELEASE"
exec npm exec --yes --package=vercel@59.11.7 -- vercel deploy --prod --yes --scope mhju0s-projects
