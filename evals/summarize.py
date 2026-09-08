"""Audit recorded release outcomes without further model calls."""

import json
import statistics
from pathlib import Path

from slice.core import SNAPSHOT, checksum, guard_intent


def main():
    result = json.loads(Path("evals/results/heldout-01.json").read_text())
    facts = {f["id"]: f for f in json.loads(SNAPSHOT.read_text())["facts"]}
    violations = []
    for run in result["runs"]:
        for turn in run["turns"]:
            answer = turn.get("answer", {})
            for f in answer.get("figures", []):
                if f != facts.get(f["id"]):
                    violations.append(
                        {
                            "turn": turn["id"],
                            "reason": "Source or figure differs from approved snapshot",
                        }
                    )
            if (
                "intent" in turn
                and guard_intent(turn["question"], turn["intent"], turn["context"])
                != turn["intent"]
            ):
                violations.append(
                    {
                        "turn": turn["id"],
                        "reason": "Intent failed explicit context guard",
                    }
                )
        if run["actual"] != run["expected"] or not run["pass"]:
            violations.append(
                {"case": run["case"], "reason": "Final task outcome mismatch"}
            )
    assert not violations, violations
    turns = [t for r in result["runs"] for t in r["turns"]]
    seconds = [t["wall_seconds"] for t in turns]
    scores = []
    for lang in ("ko", "en"):
        for trial in (1, 2, 3):
            runs = [
                r
                for r in result["runs"]
                if r["language"] == lang and r["trial"] == trial
            ]
            groups = {}
            for group in ("supported", "withheld_or_clarification"):
                subset = [
                    r
                    for r in runs
                    if (r["expected"]["operation"] in ("report", "compare"))
                    == (group == "supported")
                ]
                groups[group] = {
                    "correct": sum(r["pass"] for r in subset),
                    "total": len(subset),
                }
            scores.append(
                {
                    "language": lang,
                    "trial": trial,
                    "correct": sum(r["pass"] for r in runs),
                    "total": len(runs),
                    **groups,
                }
            )
    public = {
        "status": "PASS",
        "scenarios": 40,
        "trials": 3,
        "scenario_runs": len(result["runs"]),
        "turns": len(turns),
        "scores": scores,
        "source_value_violations": violations,
        "seconds": {
            "n": len(seconds),
            "median": statistics.median(seconds),
            "p95": sorted(seconds)[int(0.95 * (len(seconds) - 1))],
            "max": max(seconds),
            "definition": "Per application turn, includes model preflight, worker startup and PostgreSQL graph/persistence; mostly warm, first turn load-inclusive.",
        },
        "scope": "Three companies, three verified metrics, fixed historical snapshot. Agent-authored paraphrases share task families with development; not independent review or arbitrary financial language certification.",
        "runtime_network": "Application and Ollama ran under a macOS outbound-network deny policy allowing localhost only.",
        "failures_retained": "Development initially exposed guessed context and an SEC metadata adapter bug; an English follow-up was safely blocked before explicit company handling was refined. Prior benchmark Qwen fabrication and generated-prose errors remain disqualifying evidence.",
    }
    public["raw_result_sha256"] = checksum(result)
    Path("evals/release-summary.json").write_text(
        json.dumps(public, ensure_ascii=False, indent=2) + "\n"
    )
    lines = [
        "# Release evaluation",
        "",
        "| Language | Trial | Task outcomes | Supported answers | Withholding / clarification |",
        "|---|---:|---:|---:|---:|",
    ]
    for s in scores:
        a = s["supported"]
        b = s["withheld_or_clarification"]
        lines.append(
            f"| {s['language']} | {s['trial']} | {s['correct']}/{s['total']} | {a['correct']}/{a['total']} | {b['correct']}/{b['total']} |"
        )
    lines += [
        "",
        f"{len(turns)} real local turns. Median {statistics.median(seconds):.2f}s; observed p95 {public['seconds']['p95']:.2f}s; maximum {max(seconds):.2f}s. Mostly warm, first turn includes model load. No source/value mismatch in the recorded outputs.",
        "",
        public["scope"],
        "",
        public["runtime_network"],
        "",
        public["failures_retained"],
        "",
    ]
    Path("evals/RESULTS.md").write_text("\n".join(lines))
    print(json.dumps(public, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
