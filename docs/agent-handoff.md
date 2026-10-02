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

## 2026-10-01 (later)

- What changed: The owner approved D1–D17 and G1–G8. The revamp merged as PR #11. Glossary entries are now keyed by ticker and shared with Filing Digest. `slice/web/src/glossary.json` is identical to Digest's `contracts/family-glossary.json`. Filing-name aliases resolve through `company_aliases`, and `glossary.test.ts` checks that every company and metric in the ledger has names in both languages. English shows "Samsung Electronics" instead of "Samsung". Digest web family section: Digest PR #25, merged. Digest iOS number rules, search language and glossary: Digest PR #26, stacked on the owner's `feat/english-answer-screens`.
- Decisions and why: D14 holds deploy, so the new replay isn't live and Digest citations don't deep-link to the Ledger yet (G2 skipped). Ledger ratios computed in the browser are a recorded display-only exception to ADR 0008 (ADR 0013).
- Open issues: Deploy (D14) is still held. When it lifts, update the deploy allowlist and manifest, then add G2 deep links. The two glossary copies must change together. Digest PR #26 waits on the owner's branch.
- Next step: Owner decides on deploy, then does G2.

## 2026-10-01 (deploy)

- What changed: The owner lifted the D14 hold. The reading-surfaces replay is deployed to https://filing-agent.vercel.app from the reviewed manifest `docs/audits/2026-10-01-reading-revamp/artifact.json` (PR #13). Production hashes match the manifest. The portfolio (mhju0.github.io) now shows the new Agent screens and the sentence-case Digest English digest.
- Decisions and why: `recording.json` is reused byte-for-byte, so the recorded runs are unchanged. Only the UI bundle, ledger and font changed.
- Open issues: G2 (Digest citation links into the Ledger) is now unblocked. The Korean calculation chips still show "KRW" where the rest of the Korean UI uses 원.
- Next step: G2.

## 2026-10-02

- What changed: README rewritten around the live demo (184 → 74 lines), with a current screenshot at `docs/screenshots/replay-comparison-en.png`. Setup, architecture, decisions and the source guide are now linked instead of repeated. `release/github.json` matches the live GitHub About text. The Korean calculation chips now show 원/달러 (PR #15, deployed).
- Decisions and why: The owner approved the before/after README report. Every number in the README was re-checked against the verification records; the 57 policy tests were re-run.
- Open issues: G2 (Digest citation links into the Ledger). The Filing Digest walkthrough still shows old iOS screens; recapture is the agreed follow-up there.
- Next step: G2.

## 2026-10-02 (G2)

- What changed: Each ledger company heading now has a stable ticker anchor, `#ledger/ledger-<ticker>`. A `?lang=ko|en` link overrides the saved language. On mobile a scroll margin keeps a linked heading clear of the sticky header. `ledger_years` in the shared glossary lists the ledger's companies and years, and a test derives it from `ledger.json`. Filing Digest links Samsung Electronics, NAVER and Microsoft to those anchors (Digest D55). The replay was rebuilt and deployed; `recording.json` is unchanged.
- Decisions and why: Anchors use tickers rather than Korean company names to avoid percent-encoding. Links target a company section, not a single row, because Digest cites passages from later fiscal years than the ledger covers.
- Open issues: The Digest walkthrough recapture is blocked because Upstage Solar returned 403 for every call. The two glossary copies must still change together.
- Next step: None here. Recapture the Digest walkthrough once its Solar key works.
