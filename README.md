# Filing Agent

**Status: local application implemented and public replay deployed, September 8, 2026.** The React/TypeScript interface, FastAPI/LangGraph workflow, native PostgreSQL persistence and pinned Ollama/Gemma inference run on the owner's Mac. Public visitors receive a static recording of actual investigations. This repository includes private recruiting research and remains private.

Filing Agent adds conversational investigation to Filing Digest's data foundation. It uses a separately audited historical fact snapshot, interprets questions locally, and owns evidence selection, arithmetic and financial wording in code.

- [Public interactive replay](https://filing-agent.vercel.app)
- [Public engineering notes](https://filing-agent.vercel.app/engineering-en.html) · [한국어 프로젝트 소개](https://filing-agent.vercel.app/engineering-ko.html)
- [Local application setup and operations](slice/README.md)
- [Release evaluation: three trials, separately scored Korean and English](evals/RESULTS.md)
- [Implementation and verification record](docs/audits/2026-09-08-slice/README.md)
- [Durable workflow and public/private release boundary](docs/adr/0006-persisted-local-workflows-and-release-scope.md)

The measured scope is fifteen verified facts across three companies. It does not imply general financial-document reading or production cloud operations.

## Start here

| Document | What it answers |
|---|---|
| [Local model findings and measured candidate](bench/runs/2026-09-07/README.md) | 117 recorded case runs, Qwen disqualification, Gemma intent-only baseline, timings, memory and semantic failures |
| [Intent and financial-answer boundary](docs/adr/0005-local-intent-and-deterministic-financial-answers.md) | Provisional Gemma configuration and code-owned evidence, refusal, arithmetic and bilingual financial wording for the next slice |
| [Coverage audit and verified pilot](docs/audits/2026-09-07-coverage/README.md) | Fresh read-only inventory, original-regulator checks, 15 source-bound pilot facts, a reproduced Digest coverage gap, and remaining DART navigation gate |
| [Latest decisions and feasibility gates](docs/adr/0004-ledger-and-prebuild-gates.md) | Selected Ledger, visible preferences, mobile evidence without peek, saved continuation, source policy, and three approved checks; takes precedence over earlier conflicting defaults |
| [Interactive design studies](design/alternatives/README.md) | Selected Ledger refinement and earlier A/C alternatives, screenshots and prototype verification |
| [Latest integration re-audit](docs/planning/2026-09-06-integration-reaudit.md) | Fresh source, contract probes, corpus checks, verification, and relationship corrections |
| [Local-first architecture](docs/planning/2026-09-06-local-first-architecture.md) | Approved local-only application and public replay; execution/data/dependency boundaries |
| [Recruiting value of replay versus live hosting](docs/research/2026-09-06-replay-portfolio-assessment.md) | Korean/US employer evidence, project completeness, and the production-experience tradeoff |
| [Public replay and presentation brief](docs/planning/2026-09-06-public-replay-presentation.md) | Saved decision context, intended professional impression, and concrete presentation release checks |
| [Approved pre-build choices](docs/planning/2026-09-06-prebuild-interview.md) | Model latency/quality, UX, backups/diagnostics, visual direction, public artifacts, and hands-on ownership |
| [UI/UX skills assessment](docs/research/2026-09-07-uiux-skills-assessment.md) | Official Astra guidance, current skill adoption, local dependency tradeoffs, and a proposed download |
| [Four-way UI/UX skill comparison](docs/research/2026-09-07-uiux-four-way-comparison.md) | UI/UX Pro Max, Emil, Impeccable, and Sleek; recommended roles alongside antislop |
| [Approved audit decision packet](docs/planning/2026-09-06-remaining-design-decisions.md) | Six approved choices; local-first direction supersedes its hosted-service defaults |
| [Design interview and confirmed decisions](docs/planning/2026-09-06-design-interview.md) | Owner priorities, answers that supersede earlier assumptions, and the next product decisions |
| [Visual direction](DESIGN.md) | Selected Ledger layout, visible language/theme controls, and full-height mobile evidence |
| [Source catalog feasibility](docs/planning/2026-09-06-source-catalog-feasibility.md) | Available source metadata, identity-verification gaps, and conditions for reliable comparisons |
| [Detailed project plan](docs/planning/2026-09-06-project-plan.md) | Product scope, tools/API, state, evidence, failures, budgets, evaluation, milestones, KO/EN positioning and open decisions |
| [Foundation audit and Filing Digest rescan](docs/planning/2026-09-06-foundation-audit.md) | What the old foundation gets wrong or no longer reflects; current source, tests, Git state and corpus coverage |
| [Korean hiring research](docs/research/2026-09-06-korean-hiring.md) | Eight role analyses, requirement/preference distinctions, financial AI guidance, evidence matrix and source/search notes |
| [English hiring research](docs/research/2026-09-06-english-hiring.md) | Korea-based global teams versus overseas/remote roles, hiring gates, portfolio/interview evidence and source/search notes |
| [Original foundation](FOUNDATION.md) | Unchanged historical proposal from August 27–28; contains superseded assumptions and a build-start prompt that is not active for this planning phase |

## Principal recommendation

Keep Filing Digest as the flagship. The owner approved a desktop/mobile web companion for readers investigating disclosures across follow-up questions, years, and companies. It will support annual changes when figures are comparable and side-by-side company figures, starting with a curated Korean/US corpus and explicit coverage. Every displayed financial figure must link to its original filing; withhold figures lacking that evidence while preserving supported results. Korean and English support covers conversations, clarification, errors, and evidence explanations; source excerpts retain their original language and translations are labeled.

The hiring research supports these capabilities in selected roles. It does not establish a universal LangGraph screening threshold, a “top 1%” ranking, a prescribed number of portfolio projects, or a guarantee of interviews.

## Corrections that matter before implementation

1. `/digest` returns the latest period. Historical figures require `/answer.figures` and exact filtering.
2. Exact figure values, clickable source links and semantically supported narrative are different guarantees. The frozen API does not always supply all three.
3. The upstream vocabulary has seven entries, but only six reported metrics; the derived operating-margin entry does not imply an available calculation.
4. Upstream model tokens/cost are not exposed over REST. Agent-layer measurement is possible; whole-stack cost remains partly opaque.
5. A local router does not make Filing Digest's Solar-backed path offline. A “human review needed” message is not a resumable review workflow.
6. The latest local Filing Digest is on a remote review branch, ahead of public `main`; pin the exact version for reproducibility.
7. A hypothesized blocked-output leak is not a discovered bug or a completed accomplishment.

## Current scan evidence

- Inspected upstream SHA: `e1ec00911f3447f4e1317af945e98413a2d961e6` on `refactor/verification-performance-audit`; remote branch matched at scan time.
- Remote upstream `main`: `4b8855de046b247cf0ed4dbeb186e1108d86e076`.
- Latest offline test run: **403 passed, 19 intentionally skipped in 1.67 s**; Ruff and Compose validation also passed. Database integration, live model/regulator calls, and Swift tests were not run.
- Read-only corpus inventory: **8 companies, 13 filings, 1,191 chunks, 86 financial facts**.
- Existing September 5 eval artifacts: **10/10 retrieval and 14/14 full-tier passes**; these were inspected, not rerun today.

See the latest integration re-audit for exact methods and limitations. The same revision now has additional documented guard, bilingual, occurrence-selection, and saved-evidence limitations; unchanged code did not imply the earlier interpretation was complete. Filing Digest, Recruiting, original FOUNDATION, external profiles and applications were left unchanged.

## Discussion priorities

The owner confirmed Korea-based backend/applied-AI roles as the primary hiring audience, with equally strong English presentation. This is their only active project: quality and hands-on understanding take priority, with no fixed schedule or effort cap. The earlier **44–74 focused-hour core** predates the approved web interface and comparison requirements and needs replacement after scope is settled.

The approved delivery model is a public interactive replay plus a real application running only on the owner’s Mac, with no online invitations or remote live sessions. Percentage changes require comparable figures and a positive prior-year baseline; historical explanations require supporting period-specific evidence. A versioned source catalog is under feasibility review. The release needs no account system, authentication provider, invitation email, tunnel, or hosted live server. Ordinary conversations expire after 30 inactive days; explicitly saved investigations remain until deleted. The bilingual replay leads with an annual comparison, followed by company-switch and missing-evidence examples. Read-only execution is automatic within limits; a reviewer queue is outside the first release. Saved investigations preserve their original answers and evidence; an explicit rerun creates a new result. New comparisons use the latest verified, comparable figures in the supported snapshot, labeling evidenced restatements. Live execution uses a fixed verified filing collection with visible coverage and dates, updated through deliberate validation. These decisions are recorded in [ADR 0001](docs/adr/0001-preserve-evidence-across-filing-snapshots.md).

The owner approved the audited fact/evidence snapshot, independent bilingual answer path, Python/FastAPI + LangGraph + PostgreSQL + React/TypeScript/Vite stack, model comparison, and release criteria. Inference is strictly local, with no cloud fallback. Ledger is the selected visual direction. Coverage verification produced a 15-fact local pilot; measured model experiments support a provisional Gemma intent-only baseline with financial output owned by code. The local application, three-trial execution-held-out evaluation, combined memory measurement, restart/cancellation checks and DART source navigation are implemented and recorded in the September 8 audit. SEC automated browser access remains restricted. The remote-availability question is settled in [ADR 0003](docs/adr/0003-public-replay-and-local-only-live-use.md). [ADR 0004](docs/adr/0004-ledger-and-prebuild-gates.md) records the latest decisions and approved checks. The September 8 implementation and release audit take precedence over earlier proposed implementation details.

These documents contain recruiting strategy and employer-specific research. Review publication scope before making this folder public. The public source distribution includes the application README and explicit application files, excluding this private planning history.
