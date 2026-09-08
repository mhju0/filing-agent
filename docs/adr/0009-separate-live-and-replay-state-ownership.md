---
status: accepted
---

# Separate Live investigation and Replay investigation state ownership

Date: 2026-09-08. Accepted during architecture exploration; implemented and verified in the [architecture audit](../audits/2026-09-08-architecture/README.md).

Separate modules own live and recorded investigation state. The live module owns drafts, requests, polling and storage recovery; the replay module owns recording loading, scenario selection and turn navigation. Both reuse Financial figure, formula and original-filing source presentation. Use existing React tools without adding a state-management dependency. This improves locality while preserving the Ledger design and ADR 0003's static-only public replay.

Navigating from investigation A to B does not cancel A. A's eventual response updates A only, never B's conversation, draft or evidence. History shows A's status, and returning to A restores its current result. Cancellation remains explicit. The single-inference limit remains: browsing another investigation is allowed during execution, but a new inference waits until the runtime is available.

Storage recovery follows ADR 0007. Navigating away must retain an unstored result in the local application's memory and keep its recovery status discoverable. Neither switching investigations nor switching presentation language changes the result's investigation identity or accepted context. Preserve the existing recorded-replay navigation and evidence behavior during extraction; the split does not introduce live execution into replay.
