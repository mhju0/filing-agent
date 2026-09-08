# Sister-project release-readiness audit · 2026-09-09

**Decision: neither project is ready for an unconditional maintenance handoff.** The public demonstrations work, and the existing test suites pass. Additional adversarial checks found a financial-narrative guard defect in Digest, unsafe network defaults in its optional Docker setup, and two recoverable language-understanding problems in Agent. The two-company coverage pilot did not pass its expansion gate.

This is the requested consolidated review before general remediation. No application code, existing Digest corpus, Agent evidence snapshot, or public replay content changed during the audit. Proposed fixes below require the owner's review under Digest decision D49; the audit does not approve them on the owner's behalf.

## Baseline and evidence

- Filing Agent: `8d8c1767ad1f88e2eafef9487952046888e7abef`.
- Filing Digest: `4afcd9c608f90af82228a0a1625cc46efb0244e6`, after PRs #18 and #17 merged. Both repositories had no open PRs when checked.
- [Machine-readable observations](evidence.json) retain new case results, the controlled narrative probe, dependency findings, coverage qualification and restore fingerprints.
- Existing [publication](../2026-09-08-publication.md), [architecture](../2026-09-08-architecture/README.md) and [coverage](../2026-09-07-coverage/README.md) records remain dated evidence, not substitutes for this audit.
- Raw regulator responses, local diagnostic logs, screenshots and the isolated pilot backup remain private. Controlled fixtures are identified below. No paid Solar generation was used in this audit.

Digest owns ingestion, normalized facts, semantic retrieval and the iOS reader. Agent uses a separately qualified, fixed snapshot and local intent inference; it is not a live consumer of newly imported Digest companies. The pilot must not be described as an Agent coverage increase.

## Findings requiring a decision

Severity describes this project's release risk, not a CVSS rating. High findings block handoff. Medium findings need a fix or explicit acceptance; minor presentation work can be deferred.

| ID | Priority | Finding | Recommended action and acceptance check |
|---|---|---|---|
| D1 | High · correctness | Digest accepts unsupported financial prose through `/answer` when amounts use some ordinary Korean/English spellings. | Strengthen the narrative contract and guard, preserving authoritative structured figures. Add adversarial endpoint regressions; every unsupported financial claim in the probe must be blocked. Do not equate a valid citation ID with support for a claim. |
| D2 | High · unsafe default | Compose publishes PostgreSQL as `5433:5432` and the optional unauthenticated API as `8001:8000`, without a loopback address. The DB has a documented development password default. | Bind both host ports to `127.0.0.1`. Make physical-device LAN access an explicit, documented opt-in. Check resolved Compose configuration and listening addresses. No new account system is needed. |
| D3 | Medium · expansion gate | Costco's annual filing fails the existing SEC prose parser before persistence. | Keep the current qualified roster. If wider coverage is selected, make a bounded parser improvement using a recorded failing document and existing issuer regressions, then repeat the same pilot. Do not substitute another company just to turn the gate green. |
| A1 | Medium · understanding/UX | A clear Korean company correction becomes a technical interpretation error; an explicit unsupported company receives a generic clarification. | Present a localized clarification or coverage explanation with the original question preserved. Support simple corrections only where scope is unambiguous; test against accidental company substitution. |
| A2 | Medium · maintenance | Agent's GitHub workflow checks publication boundaries, but does not run its application tests or frontend build. | Add reproducible offline tests/build and isolated PostgreSQL lifecycle checks to CI. Keep actual local-model qualification separate from hosted CI. Require the relevant checks before merge. |
| D4 | Medium · maintenance | Digest main is unprotected; dependency ranges do not reproduce the installed environment exactly. | Require existing backend/iOS checks, prevent force-push/deletion, and record a reproducible dependency set with a deliberate update process. Verify a fresh environment rather than relying only on the existing venv. |
| B1 | Medium · dependency hygiene | Installed Python environments contain advisories in pip/setuptools; Digest also has a Torch advisory. GitHub's empty alert list did not establish that these local environments were clear. | Upgrade the affected tooling in a controlled environment; qualify the Torch change with KURE normalization, retrieval and persistence checks. Assess actual attack prerequisites rather than treating every scanner hit as a remotely exploitable app defect. |
| D5 | Medium · recovery qualification | Current-schema backup/restore passed after selecting PostgreSQL 16 tools. A newer default client failed restore with `transaction_timeout`; legacy-schema upgrade/restore is still unqualified. | Document matched client/server tooling and add a disposable legacy migration/restore exercise. Do not run migrations against the owner's corpus to test them. |
| D6 | Medium · defensive boundary | Digest accepts `Host: attacker.invalid` on `/health`; no trusted-host middleware is present. No permissive CORS header was returned. | Add a small host allowlist appropriate to loopback, with explicit LAN overrides. This is defense against browser-origin/host confusion; a full DNS-rebinding exploit was not demonstrated. |

### D1 reproduction and limits

The probe uses the actual FastAPI `/answer` route, answer service and narrative guards with controlled retrieval/DB fixtures and controlled model output. Its cited excerpt is only `Revenue grew on demand.` Structured figures are independent fixture values; they do not support the following claims.

| Controlled model sentence | Observed narrative status |
|---|---|
| `Revenue increased by 20 percent.` | `ok` |
| `영업이익률은 20퍼센트입니다.` | `ok` |
| `Revenue was USD 5 billion.` | `ok` |
| `Revenue was five billion dollars.` | `ok` |
| `Revenue was $5 billion.` | `blocked` · control |

The relevant implementation is `backend/app/llm/number_guard.py`, exercised through `backend/app/answers/service.py` and the route fixtures in `backend/tests/test_answer_route.py`. The current patterns recognize `%` and some digit/currency combinations but miss these alternate forms. This is a reproducible guard bypass, **not a measurement of how often Solar generates these sentences**. All existing offline tests can pass while this defect remains.

One direction is broader financial-expression detection plus source normalization. Another is a narrower generated-narrative contract that withholds financial claims and leaves amounts to deterministic figure presentation. The former preserves richer prose but needs a larger adversarial corpus; the latter reduces expressiveness and is easier to audit. Neither should promise unrestricted semantic entailment from regexes alone.

### A1 live local-model observations

Six new questions ran once each through the actual local API and pinned `gemma4:e4b` runtime. The three missing-evidence/injection cases withheld figures, and Microsoft FY2024 revenue returned the correct `245122000000` USD. No invented financial value was emitted in this small collection.

- `Tesla revenue in 2023?` produced `ambiguous_context` and asked for a company even though one was supplied. A clear unsupported-coverage message would be more useful.
- `삼성전자가 아니라 네이버의 2023년 매출액을 알려줘.` stopped with `Company interpretation conflicts with the question; rephrase with one company`. The safety guard prevented substitution, but the recovery is technical and English despite Korean UI language.
- Observed wall times were 2.91–9.32 seconds. These are single-run smoke observations, not a replacement benchmark or a general accuracy claim. Two of six questions did not receive the intended useful outcome.

### Dependency and network interpretation

Agent had pip `26.1.2` and setuptools `82.0.1`; Digest had pip `26.1.2`, setuptools `81.0.0` and Torch `2.12.1`. Scanner fixes were pip `26.2`, setuptools `83.0.0` and Torch `2.13.0`. Duplicate records for the same advisory should not be counted as independent vulnerabilities.

The [pip advisory](https://github.com/advisories/GHSA-qwm4-qh6w-59xr) concerns package acquisition, and the [setuptools advisory](https://github.com/advisories/GHSA-h35f-9h28-mq5c) concerns source-distribution exclusion on macOS. The reviewed [Torch advisory](https://github.com/advisories/GHSA-rrmf-rvhw-rf47) is rated Low and describes a local `torch.jit.script` attack path; an old scanner description calling it critical is not an appropriate application severity assessment. Exploitability in this app's KURE path was not demonstrated.

The Compose finding is a confirmed configuration issue, not a claim that this Mac was attacked or internet-accessible. Docker documents that omitted host addresses publish to all host addresses by default; local firewall and daemon settings affect reachability. See [Docker port publishing](https://docs.docker.com/engine/network/port-publishing/).

## Coverage pilot: stop before adding ten companies

Both imports ran against one new disposable database. The original corpus remained at **8 companies, 13 filings, 86 financials and 1,191 chunks** before and after the pilot.

| Company | Outcome | Qualification |
|---|---|---|
| LG Electronics · `066570` | Imported in 74.11 seconds | FY2025 annual filing `20260313000662`; 10 financial values, including FY2024 comparatives; 115/115 chunks indexed. All ten stored amounts match the consolidated DART response. Korean and English business-segment queries each returned five hits; reviewed leading excerpts describe the requested businesses and products. |
| Costco · `COST` | Failed in 1.31 seconds | `SecDocumentParseError`: Item 1 (Business) heading region could not be located with the expected Item 1A boundary. No Costco normalized filing was persisted. |

LG's qualification covers regulator-value matching and retrieval, not full generated-answer correctness, every possible accounting label, or separately ingested annual reports for all comparative years. The source has current-year and comparative values; their existence does not establish broad historical coverage.

The pilot database was dumped and restored to a second disposable PostgreSQL 16 database. Canonical row fingerprints matched for companies, filings, financials and chunks, including vector contents. This qualifies that backup's current-schema round trip, not historical migrations. The first attempt with newer default PostgreSQL tools failed; repeating with matching version-16 tools passed.

**Recommendation:** fix the existing correctness and release controls first. Then timebox SEC parser qualification using Costco. Ten more companies are worthwhile only if onboarding can pass the same repeatable checks without per-company exceptions. Arbitrary-company discovery and in-app ingestion remain separate features.

## Verification coverage

| Area | Filing Agent | Filing Digest |
|---|---|---|
| Automated application checks | 17 lifecycle/application tests and 31 benchmark/policy tests passed in this audit. | Baseline qualification immediately before this audit: 403 offline tests passed; 19 intentionally skipped. Six DB smoke and 13 persistence tests passed in disposable databases. |
| Live model/retrieval | Live local browser comparison passed; six new API edge cases recorded above. No cloud inference. | LG uses real DART ingest and local KURE retrieval. No fresh Solar quality evaluation; controlled-output guard test failed. |
| Persistence/recovery | Tests cover saved-result preservation, expiry, backup/restore, restart/checkpoints and uncertain commits. Browser checks exercise storage failure/retry, confirmed discard and late-response navigation. | Fresh pilot dump/restore passed with matched tools. Legacy migration qualification remains open. |
| Public hosting | Deployed replay browser checks passed; no live API requests. Notes/video/download flows passed, including failed-recording recovery. | Deployed Pages walkthrough passed at 320/390/768/1440 pixels in normal/reduced motion. All requests remained on the static Pages origin. |
| Web accessibility | Tested KO/EN, light/dark, 320/390/desktop, focus return/trap, Escape, keyboard and automated WCAG A/AA checks. | Eight viewport/motion combinations had no horizontal overflow, JS errors or automated WCAG violations. Animation controls toggled correctly; GIFs were not loaded before interaction. |
| Visual review | Evidence and financial hierarchy remain readable; mobile composer occlusion is transient while scrolling and both figures remain reachable. No demonstrated blocked figure. | Desktop/mobile landing captures reviewed after loading lazy images. Current native iOS build succeeded; Korean start screen rendered at default and largest accessibility text size, with system light/dark. |
| Native app | Not applicable. | Current-baseline CI passed 36 unit tests and one UI flow. Simulator capture used `-ui-testing` fixtures, not live corpus answers. Full native screen-reader and every-screen Dynamic Type qualification remain open. |
| Dependencies | npm audits for app and verification tools reported zero findings; `pip check` passed. Python advisories above remain. | `pip check` passed; Python advisories and reproducibility gap remain. |
| Source/privacy | Existing same-baseline source/archive and history scans passed; publication guard is enforced. Previously documented GitHub cached-history limitation remains unresolved. | Existing same-baseline full-history secret scan and CI passed. No new credential-bearing audit artifacts are published. |

Passing axe is not a claim of complete accessibility. Physical-device VoiceOver, every native large-text interaction, external regulator availability over time, and a fresh full installation/model download on another Mac were not qualified here. These need targeted follow-up or explicit acceptance, not a fabricated green check.

## Design, motion, content and portfolio presentation

Keep the current Ledger/research-workspace direction. There is no evidence that a redesign, more animation, live invitations or a hosted inference service would improve the core demonstration enough to justify their cost.

- **Typography and layout:** Agent's aligned figures and explicit original units are useful. Preserve tabular numeric alignment and readable Korean line breaks. Digest's native largest-text start screen scales and scrolls; qualify detail/answer screens before claiming complete Dynamic Type support.
- **Motion:** Retain immediate evidence access and reduced-motion behavior. Digest's GIF “Pause” control returns to the poster rather than holding the current frame. Rename it to “Stop walkthrough” or use video with real pause if that distinction matters; this is low-priority polish.
- **Copy:** Digest's landing claim “without letting generated prose invent the numbers” is too absolute given D1. Proposed replacement: “Financial figures come from structured DART and SEC data. Generated explanations link back to filing excerpts.” State guard limitations in the technical documentation even after targeted fixes.
- **Bilingual scope:** Agent correctly preserves past answer language while translating interface controls. Original Korean excerpts remain Korean under English UI, as designed. Digest's language toggle operates in its reader; device-locale localization and an English start screen are not currently promised. An English discovery/start surface is a small optional improvement for global visitors, not a reason to mislabel the existing implementation.
- **Sister-project story:** Show Digest's ingestion → normalized facts → retrieval/iOS boundary and Agent's qualified snapshot → intent → deterministic figures → replay boundary. Explain what was measured, what failed and why coverage is bounded. Avoid “production-grade,” “zero hallucination,” or implied live synchronization.
- **Recruiter path:** Keep one short route from project purpose to a real interaction, source evidence, architecture and measured limitations. A polished static replay remains sufficient for this portfolio scope; no online invitation is required for completion.

The prose received one humanizer pass: shorter claims, concrete responsibility boundaries and explicit test limits. No new recruiting-market claims were inferred from this technical audit.

## Proposed completion sequence

1. **Correctness and local security:** D1, D2 and localized safe recovery for A1; add regression cases first. Preserve exact figures, existing corpora and pinned snapshots.
2. **Repeatable maintenance:** A2, D4, B1, D5 and D6. Verify in isolated environments, require CI checks and document matched backup tooling. Resolve the separate cached-history support item using the private prepared request; do not assume another rewrite erases cached objects.
3. **Coverage decision:** attempt a bounded Costco parser fix and repeat LG/Costco qualification only if approved. Otherwise explicitly retain the eight-company roster and close expansion as deferred.
4. **Final focused qualification:** rerun affected backend/persistence/model/browser/iOS checks; finish native accessibility gaps or record accepted limits. Update wording and evidence only after results exist.
5. **Maintenance handoff:** tag the qualified revisions, retain a private restore-tested backup, document exact commands and versions, and list accepted medium/low issues. Public pages should continue to say recorded/read-only where appropriate.

Suggested maintenance is modest: monthly dependency/CI review and a short public-demo/link smoke check; full regression and snapshot/source checks when parser, model, schema or evidence changes. Requalify a restored backup before migration. Do not schedule continuous filing ingestion or paid-model runs unless a separate need is established.

### Optional features, ranked after release blockers

| Proposal | Portfolio value | Cost and ongoing burden | Recommendation |
|---|---|---|---|
| Repeatable company qualification report | Makes coverage expansion defensible and exercises real data engineering | Small/medium tooling effort; rerun per issuer/parser change | Best next improvement if expansion resumes |
| Search/filter within the ingested roster with explicit coverage | Makes current scope easier to understand | Low if current search is clarified; no new ingestion service | Prefer accurate coverage language; Digest already filters ingested companies |
| Ten qualified additional companies | Shows parser breadth if both regulators work consistently | Variable regulator layouts and future regression fixtures | Conditional on the failed pilot being resolved |
| English Digest start/discovery copy | Reduces friction for global readers | Small UI/copy scope, bilingual maintenance | Optional after correctness |
| Arbitrary-company discovery and ingest jobs | Broader product surface | High: job states, indexing failures, quotas, parser variability and recovery | Defer from this release |
| Hosted live inference / online invitations | Limited additional evidence beyond the replay | Conflicts with Agent's chosen local-only deployment; adds operations | Do not add |
