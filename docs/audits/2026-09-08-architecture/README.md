# Architecture implementation verification

Implemented the accepted investigation lifecycle, Financial figure policy and live/replay ownership decisions in ADRs [0007](../../adr/0007-complete-results-only-after-durable-storage.md), [0008](../../adr/0008-concentrate-financial-figure-policy.md) and [0009](../../adr/0009-separate-live-and-replay-state-ownership.md).

## Findings and changes

A controlled failure at the old workflow's final persistence call reproduced a retained execution lock and cancellation entry. Terminal completion now includes timing in the durable write, and execution cleanup runs even when persistence fails. The lifecycle module retains failed writes in process memory, supports repeatable storage retries without repeating inference, and requires durable confirmation of deliberate discard. Earlier durable turns and accepted context remain intact.

Financial policy now lives in `slice/financial.py`; application execution and future intent-only benchmarks use it. Runtime transport still reuses the measured loopback helpers in `bench/run.py`. Historical experiments and their archived harness source remain unchanged.

Live and replay state have separate owners. Background responses remain attached to their investigation. Browser verification also exposed draft loss during asynchronous investigation creation and initial restoration; the composer now waits for creation and restores the selected draft immediately on reload. These are explicit defect corrections, separate from financial-policy extraction.

## Verification

- [Application tests](application-tests.txt): 17 passed, including five controlled lifecycle regressions using actual PostgreSQL with injected write failures.
- [Benchmark tests](benchmark-tests.txt): 31 passed without model generation.
- [Financial extraction](financial-equivalence.json): 1,800 complete answer dictionaries match the pre-extraction implementation exactly.
- [Browser state checks](state-verification.json): delayed background responses, storage retries, confirmed discard, draft restoration and replay isolation. Controlled responses are test doubles, not model evidence.
- The [existing live browser workflow](live-browser.json) passed against actual local inference: clarification, comparison, continuation, refresh, deletion, keyboard focus and source inspection.
- Storage-recovery views passed axe checks in Korean/English, light/dark, at 1440, 390 and 320 pixels. Representative captures: [English mobile dark](storage-en-390-dark.png), [Korean desktop light](storage-ko-1440-light.png).
- [Fresh execution capture](capture.json): real local investigations and recorded timing, plus continuation, persisted clarification and confirmed inference cancellation.

The original held-out model evaluation is not rerun or relabeled as a new architecture result. The equivalence check establishes deterministic policy preservation; the fresh capture and browser run check current integration. Memory-only recovery cannot survive local application shutdown. A database outage can prevent both retry and durable discard; the affected investigation stays blocked.

## Static release

The [replay browser checks](browser-replay/replay-browser.json) and [public-material checks](browser-release/release-browser.json) passed with application, inference and database ports closed. All observed replay requests stayed within the static origin; no live question requests occurred. The 64-file source archive passed its file-hash manifest checks and imported the financial policy, runtime and workflow from an isolated extraction using the installed dependencies.

[artifact.json](artifact.json) records the reviewed static file allowlist and hashes. [Deployment verification](deployment.json) records production publication and all 15 served asset hashes. [Production browser checks](production-browser/replay-browser.json) passed against the public domain. The public video and held-out evaluation retain their original-release provenance; the interactive replay uses the new real execution capture.

## GitHub delivery

GitHub reported `mhju0/filing-agent` as public during delivery, differing from the earlier private-repository assumption. Delivery was paused until the owner authorized public repository cleanup, history removal of private material and publication of the verified implementation. Static deployment used only the reviewed allowlisted artifact.

The verified implementation was subsequently pushed to public main after the authorized cleanup. See the [publication review](../2026-09-08-publication.md) for scope and verification.
