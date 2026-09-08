"""Assemble an explicit public source archive without private repository history."""

import hashlib
import json
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def bundle(destination):
    files = set()
    for pattern in (
        "slice/*.py",
        "slice/scripts/*.sh",
        "slice/scripts/*.py",
        "slice/scripts/*.sb",
        "slice/scripts/*.mjs",
        "slice/tests/*.py",
        "slice/web/src/*",
        "slice/web/public/*",
        "evals/*.py",
        "verification/package*.json",
    ):
        files.update(p for p in ROOT.glob(pattern) if p.is_file())
    for name in [
        "slice/README.md",
        "slice/requirements.lock",
        "slice/web/package.json",
        "slice/web/package-lock.json",
        "slice/web/tsconfig.json",
        "slice/web/vite.config.ts",
        "slice/web/index.html",
        "evals/cases.json",
        "evals/README.md",
        "bench/intent.py",
        "bench/pilot.py",
        "bench/run.py",
        "bench/scoring.py",
        "bench/memory_monitor.py",
        "bench/serve.sh",
        "bench/prompts/intent.txt",
        "docs/audits/2026-09-07-coverage/pilot-snapshot.json",
    ]:
        files.add(ROOT / name)
    # App imports reuse the measured benchmark boundary. Include the small supporting
    # fixtures so users can inspect/reproduce that contract without personal research.
    files.update(ROOT.glob("bench/fixtures/*.json"))
    files.update(ROOT.glob("bench/prompts/*.txt"))
    files.update(ROOT.glob("bench/tests/*.py"))
    files.update(ROOT.glob("bench/cases.json"))
    files.update(ROOT.glob("bench/pilot-cases.json"))
    if destination.exists():
        raise ValueError("Choose a new source archive path")
    manifest = {
        str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(files)
    }
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            name = str(path.relative_to(ROOT))
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 8, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100755 if path.suffix == ".sh" else 0o100644) << 16
            archive.writestr(info, path.read_bytes())
        archive.writestr("SOURCE-MANIFEST.json", json.dumps(manifest, indent=2) + "\n")
        archive.writestr("README.md", (ROOT / "slice/README.md").read_text())
    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(bundle(args.destination), indent=2))
