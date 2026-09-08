# Use local intent interpretation and deterministic financial answers in the bounded slice

Date: 2026-09-07.

Status: provisional baseline for the already approved vertical-slice feasibility check. This is not final production-model selection or a release approval.

## Evidence

The [local benchmark](../../bench/runs/2026-09-07/README.md) completed 117 case runs and 141 local chat responses on the owner's M1 Pro Mac with 16 GiB RAM. Both requested models failed the original full-answer/source JSON contract. Both later selected correct evidence IDs while generating a false Samsung revenue-increase sentence. Qwen3 8B additionally fabricated absent R&D as zero and substituted another company's evidence for a missing-year follow-up. It is disqualified under the owner's refusal-quality rule.

Gemma 4 E4B did not fabricate missing amounts in the measured cases, but generated inconsistent success/refusal fields. A final experiment restricted it to intent interpretation and moved policy and financial answer construction entirely into code. That bounded pipeline passed 33/33 case checks across eleven cases, including 39 parsed turns. Earlier failures remain in their own reports; the narrower experiment does not make them passes.

## Bounded implementation baseline

Use local `gemma4:e4b`, digest `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`, with Ollama 0.33.3 for the next feasibility slice. Start with the measured intent configuration: context 4096, output cap 256, temperature 0, seed 42, thinking disabled, JSON Schema output, one loaded model and serial generation. Preserve the local-only server configuration and model-origin checks. Re-qualify model/runtime/config changes rather than silently following a mutable tag.

The model interprets company, metric, fiscal years, requested basis and action. It does not author financial values, source objects, arithmetic, comparison direction or refusal policy. Code resolves the verified snapshot, verifies company/metric/period/basis/currency and provenance, calculates with Decimal, and produces the financial answer and refusal wording from shared bilingual resources. Generated explanation is optional future work requiring its own grounded claims and evaluation; unvalidated prose cannot be displayed merely because its digits look safe.

This refines the earlier table-to-model assumption. For the measured successful path, the model does not need filing text or financial values. A deterministic extraction and source-verification layer still owns the filing-data foundation. Filing Digest remains a pinned, read-only partner; no Digest cloud inference path was invoked or modified.

## Limits and trade-offs

The measured warm single-turn intent cases took 1.47–1.81 seconds, and the first run after unloading took 6.37–10.55 seconds including the longest two-turn case. This is a narrower task than the original benchmark and is not a whole-application SLA. Peak sampled Ollama RSS in the final experiment was about 4.38 GiB; existing applications and earlier experiments left substantial system swap. Whole-app memory headroom remains unproven.

The benchmark covers a known three-company, three-metric verified catalog and an explicit R&D refusal probe, not arbitrary financial investigation. Curated financial wording reduces flexibility but makes claims and translations inspectable. JSON Schema helps output structure; it does not prove the interpreted intent is correct. The test oracle never participates in runtime selection or answer construction.

Before widening beyond the slice, evaluate unseen phrasing, additional aliases and unsupported metrics, relative/ambiguous years, negation and longer follow-ups. Validate explicit company changes against accepted context. Preserve pending clarification separately from accepted completed context; the benchmark tests the initial clarification, not durable clarification continuation. Keep source taxonomy distinctions and fiscal-period definitions rather than treating every consolidated or net-income label as interchangeable.

The next approved check remains a complete question → intent → verified evidence → code calculation/answer → save → static replay slice. Verify clarification recovery, cancellation, interrupted-step retry, persisted original evidence, refreshed-result lineage, replay without the Mac, and combined UI/backend/model memory. Public DART destination reliability and authentic public replay remain open gates.

## Alternatives retained

- **Full-answer generation:** tested and unsuitable as currently configured because correct source selection coexisted with wrong arithmetic, wording, formatting or policy state.
- **Evidence-ID selection plus generated prose:** faster and easier to parse, but still failed semantic and refusal-state checks. Valid IDs alone are insufficient.
- **A second grounded prose pass or another local model:** possible future experiments if the narrow product needs more expressive explanations. Retain raw failures and evaluate new configurations independently; do not restore the rejected Qwen candidate by ignoring its fabrication.
- **Cloud fallback:** excluded by the owner's explicit local-only constraint.
