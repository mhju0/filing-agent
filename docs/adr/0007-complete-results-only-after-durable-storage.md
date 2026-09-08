---
status: accepted
---

# Complete results only after durable storage

Date: 2026-09-08. Accepted during the architecture exploration; implemented and verified in the [architecture audit](../audits/2026-09-08-architecture/README.md).

Verified financial figures may remain visible while final persistence is in progress, but completion requires durable results and execution metadata. Save, Continue and Refresh remain unavailable until that point. This refines ADR 0006's completion semantics without changing saved-investigation immutability or local-only inference.

If persistence fails after verification, retain the result in memory, identify the storage failure clearly, and offer an explicit retry of persistence without repeating inference. Release execution resources even when persistence fails, and prevent new turns in the affected investigation until its state is reconciled. After application shutdown, recovery uses only durable records and explains any unavailable result; memory retention is not a durability guarantee.

The trade-off is a distinct persistence-recovery path instead of forcing a new model result or hiding already verified figures. The existing explicit inference-retry rule remains in force. The behavior below is accepted; the lifecycle module owns queueing, stage receipts, finalization and storage recovery.

## Recovery and deliberate discard

Use “Couldn't store this result” and “Retry storage” for persistence failure. Keep “Saved investigation” reserved for the existing explicit retention choice. Explain that closing the local application can lose the in-memory result.

Readers may navigate away while the local application retains the pending result. History identifies the affected investigation as “Storage failed.” Other investigations remain usable when storage is healthy; new turns in the affected investigation stay blocked until reconciliation. Permit repeated explicit storage retries without duplicate turns or repeated inference. These retries are separate from the existing one-retry limit for inference.

Offer “Discard unstored result” with confirmation. Preserve earlier durable turns and their accepted context. If storage is unavailable, keep the investigation blocked until the failed attempt's outcome can be recorded durably. Discard is deliberate and never presents the attempt as complete.
