#!/usr/bin/env python3
"""Verify recorded results with the exact archived harness that produced them."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

BASE = Path(__file__).resolve().parent
EVIDENCE = BASE / 'runs/2026-09-07'


def main():
    with tempfile.TemporaryDirectory(prefix='filing-agent-benchmark-') as directory:
        root = Path(directory).resolve()
        with zipfile.ZipFile(EVIDENCE / 'harness-source.zip') as archive:
            for entry in archive.infolist():
                target = (root / entry.filename).resolve()
                if not target.is_relative_to(root):
                    raise ValueError('Archive member escapes verification directory')
            archive.extractall(root)
        recorded = root / 'bench/runs/2026-09-07'
        for suite in ('original', 'pilot', 'intent'):
            destination = recorded / suite
            destination.mkdir(parents=True)
            shutil.copy2(EVIDENCE / suite / 'results.json', destination / 'results.json')
        shutil.copy2(BASE / 'results.json', root / 'bench/results.json')
        snapshot = Path('docs/audits/2026-09-07-coverage/pilot-snapshot.json')
        (root / snapshot.parent).mkdir(parents=True)
        shutil.copy2(BASE.parent / snapshot, root / snapshot)
        # The original verifier checks input hashes, recalculates scores and binds sources.
        subprocess.run([sys.executable, str(root / 'bench/verify_results.py')],
                       cwd=root, check=True)


if __name__ == '__main__':
    main()
