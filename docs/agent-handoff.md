# Agent handoff

## YYYY-MM-DD

- What changed:
- Decisions and why:
- Open issues:
- Next step:

## 2026-10-01

- What changed: Uncommitted revamp on `feat/reading-experience-revamp`. The web app now has Overview, Recorded runs, Ledger and 공시 Guide views, plus a tested `format.ts`, a `ledger.json` export (`slice/scripts/ledger.py`), the Filing Serif KR display subset, family tokens with 2px corners, global keep-all line breaking, and restyled engineering notes. Line-break detector went from 84 issues to 0, and axe from 16 to 0.
- Decisions and why: Ledger ratios are derived in the browser with BigInt rounding that matches ROUND_HALF_UP, so the Python policy is untouched. keep-all is applied globally because English pages contain Korean text. The font is renamed because the OFL Reserved Font Name rule applies to the subset. All of these are pending owner approval (D1–D17 in the review report).
- Open issues: Owner approval needed before any commit or PR. Python tests not run (no local Postgres). Live mode was checked only against a mocked API. The English ledger table at 360px scrolls about 20px. The new replay is not deployed: the deploy allowlist and manifest need updating. Filing Digest proposals G1–G8 have not been started.
- Next step: Apply the owner's decisions, commit in the five planned steps, update DESIGN.md, open a PR, and merge only after CI passes.
