# Filing Digest coverage audit and verified pilot evidence

Date: 2026-09-07. Scope: the first bounded feasibility check approved in [ADR 0004](../../adr/0004-ledger-and-prebuild-gates.md). All writes are in Filing Agent. Digest source and database were inspected read-only; no migrations, ingestion, model calls, or upstream edits were performed.

## Outcome

**The data path is feasible for a bounded local pilot. Public-release evidence readiness is still conditional.** All 86 stored facts match regulator API amounts and have matching value/period evidence in the captured original filings. This does not mean every possible comparison or financial interpretation is verified. A 15-fact pilot additionally binds exact metric labels, periods, units, source identities and evidence locations for Samsung, NAVER and Microsoft.

The three Korean replay scenarios can keep their intended companies and dates. Samsung 2022 and NAVER 2023 require explicit Agent-owned evidence supplements; they are not in the current Digest corpus. No successful model run or recorded investigation exists as a result of this audit.

Five existing DART public-viewer links returned a denial page titled `거부`, despite HTTP 200. Their content was obtained through the separately authorized OpenDART document API. **Do not report those five links as accessible or ship them as verified navigation.** The new NAVER 2023 viewer link is derived from its verified receipt and remains untested following the same-host denials. The eight stored SEC original-document URLs downloaded successfully. No alternate-IP, disguised-agent, or denial-bypass approach was used.

## Pinned input and read-only boundary

| Item | Result |
| --- | --- |
| Digest revision | `e1ec00911f3447f4e1317af945e98413a2d961e6` |
| Branch | `refactor/verification-performance-audit` |
| Before/after Git status | Identical; only preexisting `?? docs/CLAUDE_ENV_INVENTORY.md` |
| DB server | PostgreSQL 16.14, Homebrew, aarch64 |
| SQL transaction | `REPEATABLE READ READ ONLY`; default read-only enforced at connection, 10-second statement timeout, rollback |
| Counts | 8 companies, 13 filings, 86 facts, 1,191 chunks |
| Corpus fingerprint | `5e0cdc3793529dc1f947e0dd37ad63f5f76f3dfebb94dc04f4085783eea33f67` |
| Fingerprint scope | Company/filing/fact columns; chunk identities, metadata and text hashes. Embedding values excluded. |
| Source acquisition | 31 saved regulator responses: 13 stored filing URLs, 6 DART financial responses, 4 SEC companyfacts responses, 6 DART document ZIPs, 2 DART filing-list responses |

The source corpus and SHA match the earlier audit, now freshly checked. Remote Git refs and Digest's general test suite were not rerun; neither is necessary to establish this data snapshot. Docker was not running, but the documented Homebrew database was available; no service was started. Existing credentials were read internally for database/OpenDART access and the SEC contact header. No credentials, contact header, connection string or authenticated request URL is saved in the artifacts.

## Coverage matrix

This table describes **existing Digest observations**, not all facts available from the regulators or final application coverage. The [86-row CSV](coverage.csv) includes exact values, company, metric, dates recovered from sources, units, basis, filing identities, titles, URLs and verification status. [Fact checks](fact-checks.json) retain API matches and original-document candidates.

| Company | Regulator | Existing fact periods | Existing reported metrics | Count | Main qualification |
| --- | --- | --- | --- | ---: | --- |
| Samsung | DART | 2023, 2024, 2025 | Revenue, operating income, total net income, parent-attributable net income, basic/diluted EPS | 18 | 2022 absent; 2024 comes from the 2025 filing; public viewer denied |
| Hyundai | DART | 2024, 2025 | Same six | 12 | Net income must remain distinct from continuing operations; public viewer denied |
| NAVER | DART | 2024, 2025 | Revenue, operating income, basic/diluted EPS | 8 | 2023 absent; net-income rows exist in source but are filtered out upstream; public viewer denied |
| SK hynix | DART | 2024, 2025 | Revenue, operating income, basic/diluted EPS | 8 | Net-income rows exist in source but are filtered out upstream; public viewer denied |
| Apple | EDGAR | FY2023, FY2024, FY2025 | Revenue, operating income, net income, basic/diluted EPS | 15 | FY2023 is 371 days; FY2024/FY2025 are 364 days |
| Microsoft | EDGAR | FY2023, FY2024, FY2025 | Same five SEC metrics | 15 | Fiscal year ends June 30, not December 31 |
| NVIDIA | EDGAR | FY2026 only | Same five SEC metrics | 5 | No existing two-year comparison; FY2026 runs 2025-01-27 through 2026-01-25 |
| Tesla | EDGAR | FY2025 only | Same five SEC metrics | 5 | Source labels `NetIncomeLoss` as income attributable to common stockholders; do not assume equivalence to DART total profit |

There are 17 company/period combinations. All 86 persisted facts lack start/end dates and have scale 1. The audit recovered date ranges from original DART statement headers and SEC inline-XBRL contexts, cross-checking the latter with companyfacts. Those recovered dates exist in Agent audit artifacts; the upstream records are unchanged. Twenty 2024 DART facts belong to filings labeled 2025, so filing period and fact period cannot share one field.

## Findings that change implementation

### 1. The existing demonstration values are correct, but their source wording is not interchangeable

OpenDART's financial response and the original Samsung 2023 business report both contain revenue of **258,935,494 백만원** for 2023 and **302,231,360 백만원** for 2022. The original connected statement is `2-2. 연결 손익계산서`, with exact calendar-year ranges. Its revenue row reads `영업수익 (주29)`, while the earlier issuer-PDF prototype displayed `매출액`.

Keep `revenue` as the canonical metric and accept both Korean aliases. Keep the exact selected source label in evidence. The source's current 2025 statement uses `매출액`, which also shows why one static label per company is insufficient. Source labels belong to source occurrences.

NAVER's 2023 consolidated comprehensive-income statement reports **9,670,643,576,585 원**, equivalent exactly to **9,670,643.576585 백만원**, under `영업수익 (주35)`. The current benchmark's numeric value is confirmed, but its KIND-hosted integrated-report provenance should not be mistaken for this newly captured DART evidence.

The official [OpenDART financial API guide](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS003&apiId=2019020) defines the receipt, account ID/name, statement type, currency, annual report code and current/prior-period fields used here. The [document API guide](https://opendart.fss.or.kr/guide/detail.do?apiGrpCd=DS001&apiId=2019003) documents original-file retrieval by receipt. Both are evidence-acquisition services; neither performs model inference.

### 2. A reproduced Digest parser filter explains missing net-income coverage

The current `_dedup_profit_loss` keeps profit-loss-family accounts only when `sj_div == "IS"`. NAVER and SK hynix report their relevant net-income accounts under `CIS`. Running the existing pure parser against the newly captured official responses drops both available accounts for each company. This accounts for eight absent current/prior-year observations across 2024/2025.

Evidence: [captured probe](digest-cis-probe.json); upstream `backend/app/clients/dart.py:230` and `:424`. This is a confirmed filtering limitation, not evidence that the companies lack net income. Agent may bind reviewed source facts in its own snapshot; a Digest fix is separate upstream work and was not made here.

### 3. Numeric equality cannot select the source row

Several basic/diluted EPS values are identical. Samsung 2023 total profit also equals continuing-operations profit, and Hyundai has periods where those labels share a value. Matching a number anywhere in a document would attach plausible but potentially wrong evidence.

All 46 DART value candidates were disambiguated with explicit source-label rules in [dart-label-review.json](dart-label-review.json). SEC matches require the same accession, taxonomy tag, unit, amount, company identifier and duration, excluding dimensional contexts. The broad 86-row inventory remains labeled as source-supported candidates; the selected 15-row pilot has the stricter reviewed bindings. No cross-market accounting-equivalence claim follows from either result.

### 4. The missing-evidence scenario needs honest scope language

The full Samsung 2023 document contains R&D discussion, including reported amounts. Its selected consolidated income statement does not have a separate R&D row. Therefore this would be wrong: “The filing contains no R&D information.”

The pilot's truthful refusal is: “현재 검증된 연결 손익계산서 범위에는 연구개발비가 없습니다. 공시 전체에 없는 정보라는 뜻은 아닙니다.” Classify it as `outside_verified_metric_scope`, retain no answer figure, and list only the statement and verified fact index actually checked for answer eligibility. Do not animate or record a fictional whole-document search. Original-report R&D discussion was observed during this audit, but its definitions were not promoted into supported pilot facts.

### 5. Fiscal-year labels alone do not establish comparability

Apple FY2023 spans 2022-09-25 to 2023-09-30 (371 days); FY2024 spans 2023-10-01 to 2024-09-28 (364 days). Retain those as reported figures but withhold automatic percentage comparisons across the different week counts under the current conservative rule. A later policy could allow reported annual change with an explicit extra-week limitation; it should not silently normalize revenue by days.

Microsoft FY2023/FY2024 use July 1 to June 30 fiscal years. Their 365/366-day difference reflects the leap day within the same annual calendar definition. This is distinct from Apple's 52/53-week case. Dates and fiscal-year labels must be visible for US coverage. Cross-currency arithmetic and cross-regulator net-income equivalence remain unsupported.

## Pilot snapshot and replay inputs

[pilot-snapshot.json](pilot-snapshot.json) contains **15 facts**: revenue, operating income and as-reported net income for Samsung 2022/2023, NAVER 2023 and Microsoft FY2023/FY2024. Nine bind to existing Digest facts; six are explicit Agent supplements (Samsung 2022 and NAVER 2023). It is a hashed audit schema, not the production API or a new upstream ingestion pipeline. Original responses remain the numeric authority; document parsing cross-checks and locates their evidence.

The pilot intentionally pins the selected historical filing occurrences. The full audit also captured newer periods; this does not imply the pilot automatically uses every later filing or amendment. No exhaustive amendment/restatement inventory was performed.

| Scenario | Verified input / expected result | Remaining work |
| --- | --- | --- |
| Annual comparison | Samsung 2023/2022 revenue; absolute change `−43,295,866,000,000 KRW`; calculated change `−14.33%`, display approximately `−14.3%` | Run local model/pipeline and record actual execution |
| Company switch | Samsung 2023 revenue, then `네이버는?`; retain revenue/year and change company to NAVER | Test actual intent routing, not a harness that supplies the correct company silently |
| Insufficient evidence | Samsung 2023 R&D; no verified metric in pilot scope, refuse without figures | Preserve the scope wording and an honest eligibility trail |
| US coverage check | Microsoft FY2023/FY2024; revenue, operating income, net income in USD | Verify bilingual currency/date display and actual execution |

[replay-candidates.json](replay-candidates.json) records source IDs, expected results and negative controls. These are input candidates, not fabricated recordings. Current `bench/` fixtures and static UI source displays were deliberately left unchanged during this audit; a later integration must consume these evidence bindings rather than merely relabeling the old assets.

## Verification and remaining gate

[verification.json](verification.json) records a passing **offline evidence audit**: 31 response hashes, the corpus fingerprint, 86 API amount matches, 86 original-document value candidates, 46 disambiguated DART labels, and 15 pilot bindings. Deliberately corrupted value, period-column and account-tag bindings were rejected. Original regulator HTML is stored as deterministic gzip; DART document ZIPs are retained unchanged. Source storage is approximately 7.7 MiB instead of 53 MiB, without changing decompressed response hashes.

The original DART bodies are not well-formed strict XML. A narrow, bounded section/cell extractor was used for these observed filing layouts, preserving original documents and exact section slices. This is not a general DART parser or evidence that a small model can read financial tables. The model will receive only verified structured facts.

**Next approved step:** local model/runtime preflight and benchmarking with these verified inputs. The remaining public-source navigation check can proceed separately, but the public replay must not be presented as release-ready while DART viewer access remains unresolved. No new source-policy decision or blanket permission is needed to run the approved local pilot. Timing, memory use and model quality remain unmeasured.

## Reproduce the offline verification

From the Filing Agent root, using Python 3.10+ and only its standard library:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 docs/audits/2026-09-07-coverage/verify_audit.py
```

`analyze_coverage.py` regenerates the inventory/statement candidates, and `build_pilot.py` regenerates label review, pilot and scenario inputs from the captured sources. `export_corpus.py` uses Digest's existing Python environment with psycopg/dotenv to take a new read-only capture. `capture_sources.py` uses its existing httpx/dotenv dependencies and reuses saved response records; it does not silently refresh them. For a new dated audit, use a new capture directory so the pinned evidence is preserved. The scripts are audit utilities, not runtime dependencies.

No software was installed, no GitHub issue/commit/push was created, and no existing investigation or demo fixture was rewritten.

## Subsequent model check

The [local-model experiments](../../../bench/runs/2026-09-07/README.md) subsequently used this verified pilot. They preserve the same snapshot and regulator-source boundaries; they do not resolve this audit’s public DART navigation limitation.
