# Reading surfaces release · 2026-10-01

This release publishes the Overview, Recorded runs, Ledger and Guide surfaces from PRs #11 and #12 (ADR 0013). The recorded runs in `recording.json` are byte-identical to the 2026-09-10 artifact. The engineering notes still link to the [2026-09-10 verification record](../2026-09-10-final-polish/README.md), because the model, policy and evaluation did not change.

Compared with the 2026-09-10 artifact, the release adds `ledger.json` (15 verified figures from the pinned snapshot), the Filing Serif KR display subset and its OFL license. The JavaScript and CSS bundles are rebuilt.

Checks on the assembled directory before deployment:

- Line-break detector, 48 captures (7 screens × KO/EN × 1440/390, plus dark): 0 issues and no horizontal scroll.
- Source archive: 78 entries from the explicit allowlist. None are environment files, private planning or Git history.
- `npm test` (format and glossary), `npm run build` and `python3 release/check_publication.py` pass.

A follow-up rebuild the same day localizes the currency unit in the Korean calculation chips (원/달러 instead of KRW/USD). Only the JavaScript bundle changed. The detector still reports 0 issues on the comparison run.

A second rebuild on 2026-10-02 adds links from Filing Digest. Ledger company sections are anchored by ticker (`#ledger/ledger-005930`, `ledger-035420`, `ledger-MSFT`), a `?lang=ko` or `?lang=en` parameter selects the interface language, and on narrow screens a linked heading clears the sticky header. `recording.json` is still byte-identical. Checked in Chrome at 1440 and 390 px for all three anchors.

[artifact.json](artifact.json) records the exact file list and SHA-256 hashes that `release/deploy.sh` verifies.
