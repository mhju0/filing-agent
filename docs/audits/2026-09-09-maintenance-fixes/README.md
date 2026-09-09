# Maintenance fixes

Date: 2026-09-09. Follow-up to the [maintenance audit](../2026-09-09-maintenance/README.md).

## Changes

Filing Agent clears company selection when a question excludes a recognized
company, unless a bounded direct correction names another supported company.
This prevents Samsung evidence from answering a Tesla question. Regression cases
cover Korean and English exclusion wording with empty, rejected and unrelated
model company selections. Explicit same-company/metric follow-ups now retain
context for the two held-out phrases that previously requested clarification.
This remains a conservative vocabulary guard, not unrestricted language understanding.

Startup recovers blocked turns before applying retention. Recovery preserves
`touched_at`; old unsaved records still expire, saved records remain. Ordinary
retention skips active work and rechecks eligibility under the deletion lock so a
record saved or refreshed after enumeration cannot be deleted as stale.

Filing Digest rejects foreign/invalid Origin and untrusted Fetch Metadata before
route dependencies. The comparison includes scheme, host and effective port,
including explicit port zero. Sibling origins are not trusted. Native iOS requests
without browser headers and same-origin requests remain supported. TrustedHost
validation remains active. This is a local browser boundary, not authentication.
The approach follows [OWASP origin and Fetch Metadata guidance](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## Verification

The final real-model run is being finalized. Completed checks:

- Agent: 42 benchmark/policy tests and 19 PostgreSQL-backed application tests.
- The original wrong-company/old-queued reproductions now clarify without figures
  and recover successfully, respectively; the disposable database was removed.
- Digest: `make check` passes 460 tests, 21 intentional skips, lint and Compose.
  All 21 disposable database tests pass. Eight real HTTP boundary probes pass,
  including native company search and rejection of sibling-port requests.
- Frontend production build, architecture/browser state suite, static replay and
  release-material browser suites pass. No presentation assets changed.
- The rebuilt source archive validates all 63 manifest entries; all 42 policy tests
  pass from its extracted contents. Only the source ZIP changes in the static
  artifact. The [artifact manifest](artifact.json) is selected by the release script.
- Full locally reachable Git histories pass redacted Gitleaks scans. Dependencies
  are unchanged from the comprehensive audit.
- Independent Spec and Standards reviews have no unresolved confirmed findings.
  Review caught extra exclusion wording and explicit-port-zero normalization;
  preliminary model testing caught basis-correction overblocking. All three were
  fixed and given regression coverage before the final evaluation.

The original audit remains a historical record of the pre-fix versions; it is not
rewritten as a passing audit. The prior native iOS, live Digest golden evaluation,
backup restoration, corpus-integrity and dependency checks remain applicable to
unchanged components; they were not represented as newly rerun here.

## Maintenance scope

Keep the declared single-owner local applications and static public presentations.
No database migration, new feature, design integration or architecture rewrite is
part of this correction. Preserve the audit's limitations: physical-device
VoiceOver is not certified, arbitrary financial questions are not guaranteed, and
owner-only cached-history support follow-up is not verified by repository tests.


## After verification

Merge the Agent and Digest fixes through their required checks. Publish the
reviewed Agent static artifact separately so the public source download contains
the fixes; a GitHub merge does not deploy that artifact. No Digest static-site
publication is required because its walkthrough files are unchanged.

For occasional-use maintenance, run the local startup preflight before use,
back up saved investigations before upgrades, and check dependency advisories
monthly or before a recruiting demonstration. Reopen development for a reproduced
incorrect figure/source, startup failure or relevant security advisory. Otherwise,
use the apps and practice explaining their boundaries instead of adding features.
