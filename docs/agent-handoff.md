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

## 2026-10-03

- What changed: Filing Digest replaced Upstage Solar with Gemini Flash-Lite (Digest D56) and recaptured its walkthrough. Agent's engineering notes, operating guide and the Digest design mock no longer name Solar. The replay was rebuilt and deployed; only `engineering-en.html`, `LOCAL-SETUP.md` and the source archive changed.
- Decisions and why: Older audit records that mention Solar describe runs made on Solar and are left as written.
- Open issues: None.
- Next step: None.

## 2026-10-06

- What changed: Prepared local bilingual public-replay footer support links and expandable privacy/contact disclosure; corrected the Filing Digest description to source-linked summaries and Q&A. No commit or deployment yet.
- Decisions and why: Email is primary for general/private inquiries, privacy questions and deletion requests; GitHub Issues is secondary and explicitly public. Native details and existing footer tokens keep the disclosure subordinate to filing content and keyboard accessible. The disclosure covers the public replay only, browser preferences, Vercel request metadata, voluntary Gmail messages and public GitHub reports, without retention or response-time guarantees.
- Open issues: Existing Korean Overview coverage-table overflow at 320px is outside this change. Production, physical-device and full VoiceOver verification remain unperformed.
- Next step: Owner review of the local candidate. Build, nine format/glossary tests, publication checker and diff whitespace checks pass. Footer-only browser checks passed for Korean/English, light/dark and 320/390/1440px: keyboard open/close, visible focus, bounds, zero axe violations/page errors, same-origin static requests without API calls. Local evidence is in ignored `.local/contact-preview/verification.json`.

### 2026-10-06 local candidate accepted

- Root reviewed the English desktop and Korean 390px replay disclosure, including keyboard toggling and console errors. The bounded contact/copy candidate is accepted for a local commit; public deployment remains pending. Instagram preparation is deferred by the owner.

### 2026-10-06 contact/privacy publication

- What changed: Published the accepted contact/privacy copy through PR #19 (merge `05ae2c1`) and `RELEASE_AUDIT=docs/audits/2026-10-06-contact-privacy/artifact.json ./release/deploy.sh`. Production https://filing-agent.vercel.app is READY; all 26 public file hashes match the reviewed 27-file manifest (`vercel.json` is hosting configuration). Recording bytes are unchanged.
- Decisions and why: Rebuilt with the existing static assembler and source allowlist; kept older audit manifests unchanged. The source archive has 78 verified entries. CI passed publication checks, 57 benchmark tests, 19 application tests and nine frontend tests/build. Assembled footer passed KO/EN, light/dark and 320/390/1440px keyboard/axe/bounds/static-request checks. The old release harness expects an error on Overview; current Recorded runs error/reload was verified separately.
- Open issues: Existing Korean Overview overflow at 320px remains outside the bounded footer change. Physical-device and full VoiceOver coverage remain unestablished. Root verified the live alias in English desktop/light and Korean mobile/light: correct email, Issues and hosting links; replay mode; keyboard disclosure toggling; no console errors; Korean viewport document/client width both 375px.
- Next step: None for this bounded release.

### 2026-10-06 interview-readiness review

- What changed: Created a private local report at `.local/interview-review-2026-10-06/report.html` covering both projects, 30 critiques with interview answer outlines, claim corrections, demo rehearsal and owner-only questions. Product code and recruiting sources were not edited.
- Decisions and why: Recommend keeping the bounded local products, preparing a live interview rehearsal, narrowing Digest's API citation wording, and removing Solar from headline current skills while retaining dated migration experience. Recorded public demos are useful application evidence, not live or multi-user execution proof.
- Open issues: Current external profiles/attachments and credential cleanup remain unverified. Fresh local provider/native execution and physical-device checks were not performed. Chrome automation timed out twice; report visual/mobile click-through verification remains unavailable. Static source paths/anchors, script syntax, text contrast and filter/expand/reset behavior in a DOM substitute pass.
- Next step: Owner reviews the report; separately authorize any product/copy remediation. Rehearse the Mac/client live flow before an interview. The briefly requested resume layout edits were canceled before any modification.


### 2026-10-06 maintenance candidate

- What changed: Owner authorized main publication, static deployment and a dated maintenance release. Added maintenance policy/status and fixed the 320px Korean coverage table with two CSS declarations. Private report and interview material were archived in recruiting; current master skills omit Solar while historical migration evidence remains.
- Decisions and why: Close feature development, preserve the qualified model/snapshot/recordings and permit bounded defects/security/documentation fixes. No hosted backend, authentication or data migration is introduced.
- Open issues: Live model/cold-start rehearsal, independent evaluation and physical-device/full VoiceOver remain unverified or deferred. External profiles and credential cleanup are not established by this release.
- Next step: Verify the static manifest and protected CI, integrate to main, deploy/hash/browser-check and publish the dated GitHub release.

### 2026-10-06 Chrome follow-up

- What changed: Verified retired-provider key revocation and removal of its documented copy in Chrome. Current recruiting copy checks and exact blocked account/attachment steps are recorded privately in recruiting. No product code or static deployment changed.
- Verification: Started the existing local Ollama, PostgreSQL and API; Chrome executed a fresh Samsung revenue comparison, opened source evidence, saved it and restored it after API restart/reload. An unsupported metric returned no invented number. The partner API started and returned one fresh provider-backed answer; native-client and independent semantic validation are not established.
- Open issues: Logged-out recruiting profiles, attachment upload consent, actual iPhone/full VoiceOver and personal interview rehearsal remain. Dated maintenance release remains the stable product baseline.
- Next step: Follow the private Chrome checklist; no new feature work. Stop only the local processes started for this check.
