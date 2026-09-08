"""Sample whole-machine pressure and owned application processes during verification."""

import json
import subprocess
import time
from pathlib import Path

from slice.core import ROOT

from bench.memory_monitor import snapshot

out = []
for _ in range(90):
    rows = subprocess.check_output(
        ["ps", "-axo", "pid=,ppid=,rss=,command="], text=True
    ).splitlines()
    processes = []
    for row in rows:
        parts = row.strip().split(None, 3)
        if len(parts) == 4:
            processes.append(
                {
                    "pid": int(parts[0]),
                    "ppid": int(parts[1]),
                    "rss_kib": int(parts[2]),
                    "command": parts[3],
                }
            )
    ids = {
        p["pid"]
        for p in processes
        if any(
            marker in p["command"]
            for marker in (
                "uvicorn slice.app:app",
                str(ROOT / ".local/slice-postgres"),
                "ollama serve",
                "agent-browser",
            )
        )
        and "profile.py" not in p["command"]
    }
    for _ in range(5):
        ids |= {p["pid"] for p in processes if p["ppid"] in ids}
    out.append(
        {"memory": snapshot(), "processes": [p for p in processes if p["pid"] in ids]}
    )
    Path("docs/audits/2026-09-08-slice/combined-memory.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    time.sleep(1)
