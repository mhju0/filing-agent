"""Write the public figure ledger used by the Ledger view from the pinned snapshot.

The ledger carries only reported values and their source metadata. Ratios shown
in the interface are derived from these values; nothing here is calculated.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT = ROOT / "docs/audits/2026-09-07-coverage/pilot-snapshot.json"
OUTPUT = ROOT / "slice/web/public/ledger.json"

FIGURE_FIELDS = (
    "id", "company", "metric", "period", "period_start", "period_end", "basis",
    "value", "currency", "original_value", "original_unit", "source_label",
)
SOURCE_FIELDS = (
    "regulator", "filing_title", "filing_identity", "filed_at", "url", "section",
    "excerpt", "excerpt_cells",
)


def ledger():
    snapshot = json.loads(SNAPSHOT.read_text())
    figures = []
    for fact in snapshot["facts"]:
        figure = {key: fact[key] for key in FIGURE_FIELDS}
        figure["source"] = {k: fact["source"][k] for k in SOURCE_FIELDS if k in fact["source"]}
        figures.append(figure)
    figures.sort(key=lambda f: (f["company"], f["period"], f["metric"]))
    return {"schema": "filing-agent-ledger-v1", "snapshot_id": snapshot["snapshot_id"], "figures": figures}


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(ledger(), ensure_ascii=False, indent=1) + "\n")
    print(OUTPUT.relative_to(ROOT))
