# Architecture decisions

Read these records in sequence when tracing a decision. Later records refine the earlier scope; each original record retains its context and alternatives.

| Record | Decision | Later refinement |
|---|---|---|
| [0001](0001-preserve-evidence-across-filing-snapshots.md) | Preserve saved evidence across snapshot changes | 0006 records the implemented persistence, Continue and Refresh behavior |
| [0002](0002-own-evidence-and-prefer-local-execution.md) | Own verified evidence and prefer local execution | 0003 settles local-only live use; 0005–0006 define the model and runtime boundary |
| [0003](0003-public-replay-and-local-only-live-use.md) | Public replay with live execution on the owner's Mac | 0006 records export and release implementation |
| [0004](0004-ledger-and-prebuild-gates.md) | Select Ledger, expose preferences and simplify mobile evidence | 0005–0006 record the subsequent feasibility and implementation decisions |
| [0005](0005-local-intent-and-deterministic-financial-answers.md) | Restrict the local model to intent; construct financial answers in code | 0006 carries this measured baseline into the application |
| [0006](0006-persisted-local-workflows-and-release-scope.md) | Persist local workflows and define the static public release | See the dated release audit for measured outcomes |
| [0007](0007-complete-results-only-after-durable-storage.md) | Require durable completion and retry failed persistence without repeating inference | [Implemented and verified](../audits/2026-09-08-architecture/README.md) |
| [0008](0008-concentrate-financial-figure-policy.md) | Give Financial figure policy one shared owner without expanding coverage | [Implemented and verified](../audits/2026-09-08-architecture/README.md) |
| [0009](0009-separate-live-and-replay-state-ownership.md) | Separate live/replay state and keep background results attached to their investigation | [Implemented and verified](../audits/2026-09-08-architecture/README.md) |

| [0010](0010-natural-followups-and-specific-clarification.md) | Interpret natural follow-ups and ask only for missing information | First-use flow verification |
| [0011](0011-clarify-unhandled-company-pairs.md) | Clarify named company pairs outside verified coverage | Policy regression tests |
| [0012](0012-responsive-continuity-for-reading.md) | Use interruptible continuity for evidence and modal reading surfaces | Supersedes 0004's immediate-transition prototype constraint |

ADR 0002's discussion of possible cloud benchmarks or fallbacks is historical. The implemented boundary is local inference only, as detailed in 0005–0006. The [release audit](../audits/2026-09-08-slice/README.md) records verification rather than changing the decisions.

[Documentation index](../README.md)
