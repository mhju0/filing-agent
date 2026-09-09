# Maintenance readiness audit

Date: 2026-09-09. Scope: Filing Agent `9d9d638` and Filing Digest `9a67824`.
Comparison baseline for both: `release-qualified-2026-09-09`.

**Decision: not ready to close development yet.** Two reproducible Agent defects
need correction before occasional-use maintenance. A bounded Digest browser-request
hardening change is also recommended. No new features or architecture rewrite are
needed. This audit changes no application code or production deployment.

The checks cover the declared single-owner local applications and static public
presentations. They do not certify hosted multi-user operation, all possible
financial questions, every device, or an independent penetration test.

## Standards

**P2: Digest accepts cross-site requests that can trigger local work.**
`backend/app/main.py` installs TrustedHost validation, but foreign Origin and
cross-site Fetch Metadata headers do not stop the GET company-digest route.
A dependency-mocked TestClient request with local Host and foreign Origin reached
the digest builder once, as did a native request; an untrusted Host was rejected.
The real builder performs embedding retrieval and can invoke Solar on a cache miss.

This demonstrates a missing server-side boundary, not browser exploitation or
response exfiltration. Browser local-network restrictions vary, the company UUID
must be known, and same-origin policy limits response reading. Reject cross-site
browser requests while preserving native requests without browser headers; add
regression coverage. OWASP's [Fetch Metadata and origin guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
provides the relevant defense pattern. Neither application is exposed publicly
by this finding.

No actionable architecture regression was found. Recent changes are presentation
assets. Repeated design markup is comparison material, not a reason to refactor
runtime. Agent request boundaries, parameterized SQL, explicit export/source
allowlists, backup validation and permissions, Digest XML handling, and separated
financial/lifecycle responsibilities were reviewed without another confirmed issue.

Standards: one finding, worst P2 local-work request hardening.

## Spec

**P1: a rejected company can supply the financial answer.**
`slice/core.py` forces the sole recognized supported company into the intent, even
when it is explicitly negated in favor of an unsupported company. Both
“삼성이 아니라 테슬라 2023년 매출액은?” and
“Not Samsung, but Tesla revenue in 2023?” produce Samsung FY2023 revenue in the
deterministic guard-to-financial-policy reproduction. This violates ADR 0006's
“No invalid context becomes financial evidence” requirement. The amount is a real
Samsung value, but it is the wrong company's evidence for the request. Existing
correction tests omit the one-known-negated-to-unknown combination.

Two additional real API/model runs reproduced the wrong-company answer in both
languages. The finding is not limited to a synthetic model-intent fixture.

**P1: a long-idle interrupted investigation can prevent startup.**
`Store.recover()` calls `history()` before recovering interrupted attempts.
History deletes expired unsaved records; deletion refuses queued/running/saving/
storage_failed records. A 31-day-old queued investigation therefore raises
“Cancel and wait before deleting a running investigation” during startup recovery.
This was reproduced against a newly created disposable PostgreSQL database, which
was removed afterward. Interruption and expiry were separately tested before;
their combination was not. Resolve recovery/expiry ordering and test restart after
long idle time, alongside preservation of saved records.

Spec: two findings, worst P1 wrong-company evidence and long-idle startup failure.

## Executable checks

| Area | Current evidence |
| --- | --- |
| Agent application | 17 PostgreSQL-backed application/lifecycle tests pass |
| Agent policy | 39 benchmark/policy tests pass |
| Agent real model | 120 scenario runs / 138 turns: 114 exact outcomes pass; each language in each trial scores 19/20 (95%) |
| Agent frontend | Production build passes |
| Agent state ownership | Existing architecture browser suite passes background ownership, storage recovery, draft restoration, and replay isolation checks |
| Agent live interface | Actual inference browser suite passes clarification, comparison, save/reopen, continuation, refresh, preserved answer language, draft/deletion and source inspection |
| Agent real cancellation | Actual model request cancels; no context is accepted and the model list confirms unload |
| Agent public replay | Production browser suite passes source selection, languages/themes, keyboard/mobile behavior, axe and static-only network checks |
| Agent public notes | Both languages at 1440/390/320px pass links, playback, reflow and axe; recording-load failure/reload state passes |
| Digest offline | Lint, 436 tests, 21 intentional skips and Compose validation pass |
| Digest persistence | 21 tests pass on a unique disposable database, including smoke, atomic replacement and legacy migration |
| Digest iOS | Fresh simulator build/test passes 36 native tests and three UI flows |
| Fresh environments | Qualified locks install in new Python 3.11 environments; Digest offline suite and downloaded Agent source policy suite pass |
| Dependencies | Agent 49 and Digest 86 installed Python packages report no known advisories; application and verification npm audits report zero; pip dependency consistency checks pass |
| Repository secrets | Gitleaks scans both complete locally reachable Git histories with redaction; no leaks detected |
| Publication | Agent publication check passes; public archive's 63 manifest-listed files match current source; root archive README intentionally copies the operating guide |
| Hosting parity | All 19 public assets checked match local reviewed content; Vercel configuration appropriately returns 404 |
| Repository controls | Both main branches require CI checks and disable force push/deletion; latest main CI passes |
| Digest live API | All 24 golden cases pass: 14 full response cases and ten retrieval cases; retrieval Hit@1 0.90, Hit@3 1.00, MRR 0.95 |
| Expanded roster | 36 bilingual retrieval queries across all 18 companies return hits; this is availability coverage, not independent relevance judging |
| Digest public site | Eight combinations of KO/EN, light/dark and 1440/320px pass overflow, images, headline punctuation, centered scope cells, axe, playback controls and static-origin requests |
| Original filing links | Both DART filings open and all nine DART amounts are found; SEC automated browser denial remains an explicit limit |
| Agent local boundary | Correct Host accepted; wrong Host, foreign Origin, cross-site Fetch Metadata and missing mutation token rejected; security/cache headers present |

## Backup and corpus preservation

Digest's full working corpus was dumped using PostgreSQL 16, restored into a
separate database, and compared by complete canonical row hashes. All four tables
match: 18 companies, 23 filings, 153 financial records, 2,057 chunks. Live API
checks use the restored copy. A final read-only comparison confirms the original
working corpus is unchanged.

Agent's database was backed up before tests. A separate restored database was
used to exercise application backup/restore: existing investigations are preserved,
restored investigations receive new IDs, turns and evidence remain identical,
backup mode is 0600, overwriting is refused and checksum tampering is rejected.
The disposable Agent database was removed.

At completion, only the five investigations created by the browser verification
were removed. Original Agent investigation JSON remained equivalent after excluding
raw diagnostics, which the backup deliberately omits. The restored Digest test DB
was dropped. Audit application/model servers, the Agent database and the obsolete
mock server were stopped; the pre-existing Homebrew PostgreSQL service was retained.

## Qualification limits and next steps

The initial Agent model evaluation ran with the inference endpoint unavailable;
all cases ended in execution errors. That failed run is retained separately and
is not counted as a model-quality result. Evaluation was repeated only after the
pinned runtime preflight passed.

The fresh [evaluation summary](model-evaluation.json) meets the existing 95%
per-language/per-trial aggregate threshold, but is lower than the historical
100% result. In all three trials, “같은 회사의 2022년 수치를 보여줘” and
“Keep the same company and metric, but show FY2022” request the company again
instead of retaining NAVER and reporting missing-period evidence. The current
bounded follow-up guard causes this safe but unnecessary clarification. Preserve
the historical evaluation as historical; do not present it as a fresh result.
The wrong-company defect found outside this set still blocks maintenance despite
the aggregate threshold passing. Model and CPU embedding work overlapped during
part of this audit, so its timing is not a clean performance comparison.

Physical-device VoiceOver, exhaustive native Dynamic Type combinations, and a
fresh install/model download on a different Mac are not certified. Simulator UI
checks and fresh environments on this Mac do not substitute for those checks.
The owner-submitted GitHub cached-private-history removal request remains a separate
unverified follow-up; a clean current Git scan cannot prove cache removal.

The approved family design remains a prototype. Integrating it is optional final
polish and is not required to fix the maintenance blockers. Existing recordings
remain bounded historical evidence, not live public inference or broad financial
accuracy claims.

Close the two Agent defects with regression tests and targeted real execution,
address or explicitly accept the Digest boundary finding, then recheck affected
release artifacts. Preserve a monthly dependency/CI/public-link check, with fuller
qualification only when model, parser, schema or evidence changes.

Raw logs, private backups and reproducible probes remain in the ignored
`private/maintenance-audit-2026-09-09/` directory. Earlier verification records
were preserved; no production publication occurred during this audit.

The [evidence index](evidence.json) pins the tested revisions and hashes the retained
private evidence without exposing backups or diagnostic payloads.
