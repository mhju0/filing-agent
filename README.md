# Filing Agent — planning workspace

**Status: research and planning only, September 6, 2026.** No application has been built. This workspace is connected to the private [mhju0/filing-agent repository](https://github.com/mhju0/filing-agent).

Filing Agent is a proposed conversational companion to Filing Digest. Its purpose is to carry the intended company, financial metric and fiscal period across follow-up questions, handle failures explicitly, and evaluate the resulting conversation behavior.

## Start here

| Document | What it answers |
|---|---|
| [Detailed project plan](docs/planning/2026-09-06-project-plan.md) | Product scope, tools/API, state, evidence, failures, budgets, evaluation, milestones, KO/EN positioning and open decisions |
| [Foundation audit and Filing Digest rescan](docs/planning/2026-09-06-foundation-audit.md) | What the old foundation gets wrong or no longer reflects; current source, tests, Git state and corpus coverage |
| [Korean hiring research](docs/research/2026-09-06-korean-hiring.md) | Eight role analyses, requirement/preference distinctions, financial AI guidance, evidence matrix and source/search notes |
| [English hiring research](docs/research/2026-09-06-english-hiring.md) | Korea-based global teams versus overseas/remote roles, hiring gates, portfolio/interview evidence and source/search notes |
| [Original foundation](FOUNDATION.md) | Unchanged historical proposal from August 27–28; contains superseded assumptions and a build-start prompt that is not active for this planning phase |

## Principal recommendation

Keep Filing Digest as the flagship. Build the companion around a small, measurable improvement: correct follow-ups with exact figures, explicit missing data, bounded tool execution and durable conversation state. Make local-model comparisons and full human review separate extensions.

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
- Fresh offline test run: **403 passed, 19 intentionally skipped**; smoke, live model/regulator calls and Swift tests were not run.
- Read-only corpus inventory: **8 companies, 13 filings, 1,191 chunks, 86 financial facts**.
- Existing September 5 eval artifacts: **10/10 retrieval and 14/14 full-tier passes**; these were inspected, not rerun today.

See the audit for exact methods and limitations. Filing Digest, Recruiting, original FOUNDATION, external profiles and applications were left unchanged.

## Discussion priorities

The plan proposes a **44–74 focused-hour core**, followed by optional experiments. This is an estimate, not a deadline. Before building, settle the primary hiring audience, available weekly time, required source-link guarantee, first model and run budget. Hardware determines whether the local-model extension is worthwhile.

These documents contain recruiting strategy and employer-specific research. Review publication scope before making this folder public. A future product README should lead with implemented behavior and measured evidence, rather than publishing the entire planning bundle by default.
