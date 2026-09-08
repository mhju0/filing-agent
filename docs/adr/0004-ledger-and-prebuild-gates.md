# Select Ledger, expose preferences, and simplify mobile evidence

Date: 2026-09-07.

The owner selected the rendered Ledger alternative and requested language and theme controls directly on the page, removing the extra overflow-menu step. They accepted the recommendations on saved continuation, source policy and mobile behavior, expressed a preference to remove peek mode, and approved the three bounded feasibility checks. They continue to prioritize quality and local control over speed.

## Presentation

Ledger is the implementation baseline: two reported figures lead, calculated change is subordinate, and evidence includes a compact statement fragment. Keep its existing Pretendard, neutral palette and evidence accent as the working baseline; matching Digest's exact native font family is not necessary. A and C remain comparison studies, not competing implementation directions.

Language is a visible `한국어 / English` control with native-language labels and selected state. The separate theme button uses a sun/moon symbol and an accessible label naming the destination mode. Initially follow the system theme, persisting an explicit override. Preserve drafts and selected evidence when changing preferences. Local language changes affect controls and future answers; previous local answers retain their original language. Public replay changes to reviewed corresponding assets.

Remove mobile peek and drag detents for v1. Tapping a figure opens one full-height evidence view, with an explicit close button and preserved focus/scroll on return. Mobile replay starts on the conversation, avoiding a full-screen source that obscures the investigation on arrival. Desktop replay retains pre-opened evidence. This is an intentional mobile exception to the old universal pre-open rule.

No generic settings menu exists solely to hold these two preferences. Local runtime faults belong near the composer in readable text. Future export/import controls belong with investigation/history actions and do not justify hiding language or theme again.

## Saved evidence and original sources

Continue forks a new investigation with resolved context and the original pinned Agent-owned evidence snapshot. It does not treat old generated prose as newly verified evidence. Refresh/rerun creates a new investigation against the latest verified snapshot. Both preserve the original investigation; label continuation and rerun distinctly and show the relevant snapshot dates. If the original snapshot is unavailable, explain the failure rather than silently substituting newer evidence.

For the source question, the earlier review offered alternatives without a single explicit recommendation. Under the owner's delegation, retain the existing regulator-only DART/EDGAR production policy. Do not broaden the allowlist silently to make the current fixture pass. The Samsung IR audit PDF remains a clearly labeled static-prototype source exception and does not establish release-ready regulatory provenance. The coverage gate must resolve this; issuer-hosted production evidence would require an explicit later policy revision.

Agent owns verified snapshots as established by ADR 0002, preserving Digest provenance and regulator filing identities. A local ID never substitutes for the regulator's filing identity.

## Feasibility gates

The owner approved these checks. Approval is not evidence of completion. Execute them in dependency order; retain failing and inconclusive results.

1. **Read-only coverage audit.** Pin the current Digest revision/corpus; inventory company, metric, fiscal period, duration, basis, currency, scale, filing identity, source destination and verification status. Distinguish available facts from verified usable evidence. Include DART and EDGAR if both remain in launch scope. Do not invoke Digest's cloud inference path or modify Digest. Output an Agent-owned coverage report and a small verified pilot snapshot.
2. **Local feasibility benchmark.** Inspect the actual Mac, local runtime and installed models first; do not assume Ollama is installed. Use local-only inference, verify model tags, record model/config/context, cold and warm timing, memory pressure, strict output validity, exact figures and refusals. The three fixture cases are a smoke test, not a release evaluation. Include real evidence selection, incompatible comparisons and misleading follow-ups. Any fabricated financial figure in an insufficient-evidence case disqualifies the candidate under the owner's scoring rule. Report latency from measurements rather than selecting a promise in advance. No cloud fallback.
3. **One complete vertical slice.** After viable evidence and a local model are established, run question → context → verified figures → deterministic calculation → validated answer → saved evidence → static replay. Verify saved continuation versus refresh, cancellation, interrupted-step recovery, and replay with the Mac/model unavailable. Use actual captured results and timing; static study screenshots do not satisfy this gate.

These gates authorize bounded feasibility work, not publication or a claim that the full product is complete. No production latency promise or final model choice is settled yet. A failed gate calls for a documented local alternative or narrower verified coverage.

September 7 execution update: the [coverage audit](../audits/2026-09-07-coverage/README.md) completed the read-only inventory and produced a 15-fact source-bound local pilot. All 86 stored facts match regulator API amounts with original-document value candidates. Public DART viewer checks returned denial pages, so navigation readiness remains open. The insufficient-evidence scenario is now explicitly scoped to an unsupported metric in the verified statement snapshot: the full Samsung report does contain R&D information. The captured content supports local model benchmarking; the coverage audit alone does not establish model performance or an authentic replay.

September 7 benchmark update: the [local experiments](../../bench/runs/2026-09-07/README.md) completed 117 case runs. Qwen3 8B was disqualified for inventing an absent amount. The narrower Gemma intent-only pipeline passed 33/33 known case checks when code owned evidence selection, policy and financial wording. [ADR 0005](0005-local-intent-and-deterministic-financial-answers.md) records the provisional baseline and remaining qualification limits. The complete vertical slice and whole-app memory/cancellation/replay checks remain unverified.

## Engineering contract corrections

The previous review identified implementation corrections, recorded here so they are not lost while choosing a visual direction:

- Curated bilingual resources supply controls, errors and glossary labels. A model does not translate the UI at runtime. Missing translated content is labeled unavailable; an untranslated fallback is never labeled a translation. All three public scenarios need reviewed KO/EN content.
- Validate company, metric, period/duration, value, currency, scale, basis and evidence support before displaying a reported figure, including a partial result. Validate calculation operands and formulas in code. Prompt instructions alone cannot guarantee that generated prose contains only supported numbers.
- Comparisons may span fiscal years; incompatible durations/period definitions, bases or currencies block the relevant comparison. Use the latest verified comparable restatement within the pinned snapshot. Language never changes currency, and original excerpts retain original formatting.
- Explain arithmetic and unit choices when asked why; unsupported business causation remains out of scope. A specific section link requires a verified destination.
- Checkpoints persist workflow state; cancellation of inference is a separate runtime contract. Recovery restarts an interrupted step from persisted inputs unless finer recovery is demonstrated. Specify bounded cancellation and an honest unconfirmed/interrupted outcome if confirmation fails.
- Reattachment to an uncertain existing run and an explicit retry after terminal failure have different semantics. Retain attempt lineage and prevent duplicate execution.
- Use stable turn IDs for replay asset associations. Trap focus for modal surfaces, not the desktop evidence column or every disclosure. Interpretation-changing limitations need readable adjacent wording, and runtime state cannot rely on color or hover alone.
- Replay loads local/static assets and permits deliberate original-filing navigation, but never calls live/private/model endpoints. Verify observed browser requests and enforce a suitable content security policy; source grep alone is insufficient.
- Diagnose the failed stage before reducing scope. Another suitable local model may be tested before removing companies when the failure is model-specific.

## Research and trade-off

The installed [Emil skill](~/.agents/skills/emil-design-eng/SKILL.md) covers animation purpose, drawer easing, pointer capture, gesture interruption and reduced motion. It is guidance rather than a drop-in component. Its complexity is optional for this reading workflow.

[GOV.UK language navigation](https://design-system.service.gov.uk/components/language-navigation/) recommends native-language names, consistent placement and preserving entered data. The component is currently in trial status; this project adopts those principles, not its package or visual identity.

[Vaul's repository](https://github.com/emilkowalski/vaul) currently identifies itself as unmaintained. [Adobe's React Aria sheet example](https://react-aria.adobe.com/examples/sheet) provides runnable gesture-driven sheet code using React Aria, Motion and Tailwind, but does not itself establish a tested two-detent evidence workflow for this app. No new sheet dependency is installed. A single full-height evidence view keeps the source readable and removes detent/gesture complexity; the trade-off is that mobile readers close it to compare another answer figure.
