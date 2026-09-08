# Persist local workflows and prepare a static public release

Date: 2026-09-08. The owner requested continued implementation, verification after each section and deployment, with a pause only for a decision requiring their input. This expands the earlier bounded feasibility authorization into completion of the declared local application and public static replay. It does not authorize publishing the private planning history or exposing a live endpoint.

## Working implementation

The application is under `slice/`: FastAPI, a three-node LangGraph, a separate native PostgreSQL cluster and React/TypeScript/Vite. The measured Gemma model remains intent-only. The existing benchmark resolver is reused explicitly; its benchmark failures and records are unchanged. A future extraction into a standalone domain package can be evaluated without obscuring this provenance.

The actual graph stages are interpretation, verified-evidence resolution/arithmetic, and answer persistence. Filing search/download/extraction is absent from this fixed-snapshot path and therefore absent from its progress display. Durable step outputs are stored transactionally in PostgreSQL, with explicit retry of an interrupted stage and reuse of completed stages. LangGraph uses its PostgreSQL checkpointer for graph position and invocation identity; application-owned transactions preserve the immutable evidence and completed step results. Restart recovery checks the persisted attempt and reuses completed outputs. This is not token-level continuation or native tool calling. The checkpointer stores identifiers and stage markers, not private prompts or raw diagnostics.

Accepted completed context and pending clarification are separate persisted fields. An initial real application test exposed a company guess for a company-free question; it is retained as a failure. Company and year must now come from an explicit question or prior context. A single recognized explicit company is authoritative even if the model attempts to retain another company. Multi-company ambiguity remains guarded. Missing fields produce clarification. No invalid context becomes financial evidence.

Supported partial figures remain when another period or the requested comparison is unavailable. They retain exact sources and do not authorize an incompatible calculation. Unknown amounts remain absent, never zero.

Saved investigations cannot accept new turns. Continue creates a new investigation with the original snapshot, context and copied turns; Refresh creates a new investigation with the current approved snapshot, preserving the original and prefilling the question for deliberate resubmission. A missing original snapshot is a failure, not permission to substitute one. With only one approved snapshot, Refresh can legitimately retain the same data version.

## Local and public boundaries

Application/model/database services bind loopback. The browser API validates its exact Host, Origin, Fetch Metadata and a random local mutation token. Model calls use a fixed loopback URL, reject redirects and proxy inheritance, and verify the installed runtime/tag/digest and local architecture. Cloud inference and trace upload are disabled. Local processes running as the owner are outside this browser-origin threat boundary.

Normal application records keep interpreted intent and observable model/config/timing metadata. Raw intent JSON is an explicit diagnostic opt-in, expires after 24 hours at the next running cleanup, and never enters public replay. Private backups omit those diagnostics, preserve snapshots, refuse overwrite and restore into new investigation IDs. Deletion cannot erase external backup copies.

Static export takes only explicitly selected saved and completed investigations. The bundle includes local fonts/scripts, paired code-authored financial wording, original-language evidence and labeled question translations. It does not include a composer, history, raw diagnostics, private planning or a live/private endpoint. Browser request observation and stopped-runtime verification are release gates; static UI studies alone do not satisfy them.

DART filing-level navigation was successfully checked in a real browser for both replay filings, including their statement values. This resolves the earlier automated HTTP denial for those destinations; it does not promise future availability or exact table-cell deep links. SEC's automated browser denial is retained as a separate navigation limitation. SEC evidence was previously verified through identified regulator requests and original inline XBRL, not inferred from a denied browser page.

## Qualification

The wider evaluation fixes 120 scenarios: 80 development and 40 held out from execution, with three trials for the latter and separate language thresholds. Task families overlap, and the implementing agent authored the cases; these are bounded paraphrase checks, not independent accounting review or general language certification. Earlier failures remain visible. Final results, source revision, package versions, memory conditions and browser evidence belong in the release report.
