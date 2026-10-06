# Maintenance release

The owner closed feature development on 2026-10-06. The dated GitHub release
`release-qualified-2026-10-06` preserves this portfolio baseline. This is a
local, single-owner application plus a deployed static replay, not a hosted
multi-user financial service.

## Maintenance scope

Fix reproducible defects, security issues, documentation inaccuracies and broken
links. Requalify necessary dependency/runtime changes with evidence matching the
changed behavior. Feature expansion, new filing coverage and hosted operation
require an explicit owner decision to reopen development. Do not upgrade the
qualified model or runtime silently.

## Preserved boundaries

- Gemma interprets intent; code chooses evidence, calculates with Decimal and
  renders supported financial answers. The model does not write them.
- The approved historical catalog contains 15 figures for Samsung Electronics
  FY2022–2023, NAVER FY2023 and Microsoft FY2023–2024. Unsupported metrics may
  exist in the source filing but are not qualified by this catalog.
- Refresh uses the current approved snapshot; it does not fetch newer filings.
- Persisted completed stages can resume/retry. Token streams do not resume.
  A result not successfully saved to PostgreSQL is not durable.
- Public visitors view recorded runs. No visitor query connects to the Mac.
- Evaluations are project-authored bounded scenarios, not independent financial
  accuracy certification. Hardware and timing claims remain dated.

## Operating and interview checks

Use the [operating guide](../slice/README.md). Before a live interview, start the
local services, verify the pinned model and one supported question, then rehearse
evidence inspection and save/continue behavior. Keep the public recording as a
fallback. No fresh live-model or cold-start qualification is claimed by this
maintenance release.

## Deferred work

Independent questions and semantic review, wider coverage, physical-device and
full VoiceOver checks are not acceptance claims for this baseline. Multi-user
capacity, authentication and cloud operation need a new design if scope changes.
Private recruiting notes and external job-site cleanup are tracked outside this
public repository.

## Release evidence

The [closeout audit](audits/2026-10-06-maintenance/README.md) records this release.
Older model and source qualification remain in the [verification index](audits/README.md).
The public release remains available for portfolio review; original code has no
open-source license grant.
