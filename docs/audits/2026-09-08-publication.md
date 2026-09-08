# Public repository review

The verified local application and static replay are now represented on GitHub. The repository remains public; private planning and recruiting research stay local.

## Publication boundary

- Removed private planning, research and presentation-process records from the published branch history, retaining engineering commits and their dates. Original history and local documents were backed up outside the repository before rewriting.
- Replaced the personal commit email with the account's GitHub no-reply address. Redacted home-directory prefixes in diagnostic metadata; financial snapshots and recorded model results retain their original bytes.
- Expanded `.gitignore` for private documents, credentials, local conversations, database files, backups, diagnostics, editor settings, dependencies and generated releases.
- Added `release/check_publication.py` to reject tracked ignored paths and Markdown links to unpublished files. A controlled index containing six forcibly added private/generated paths was rejected. GitHub Actions runs the check on pull requests and main.
- Kept current architecture decisions, regulator evidence, benchmark results, evaluation records, design studies and implementation code public. The documentation index links only public material.

A direct lookup confirmed that GitHub still serves an old planning file by its old commit hash after the rewrite. Removing branch history does not erase downloaded copies or GitHub's cached, unreferenced objects. [GitHub documents cache removal through Support](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository), subject to its sensitive-data criteria. No forks, releases, issues or pre-existing pull requests were present during the review.

## Verification

Gitleaks scanned the original published history, the filtered nine-commit history, the public working tree and 19 expanded archives. The only initial detections were 218 public `api_sha256` checksum fields. A narrowly scoped rule permits that exact JSON field with a 64-character hexadecimal digest; the default credential rules remain enabled. Reviewed scans reported no credential findings. This is a bounded automated scan, not a guarantee that no sensitive content exists.

All 17 application tests and 31 benchmark tests passed, and the production frontend built successfully. An additional check exposed a stale historical benchmark verifier: it compared refactored source with old input hashes. The verifier now runs the archived harness in a temporary directory and checks 117 recorded case runs and 141 actual responses without inference or changes to historical results.

All 15 served production assets matched the reviewed release hashes. The public site remains at https://filing-agent.vercel.app. Repository cleanup changes documentation and publication controls; it does not expose the local question API or change the replay deployment boundary.

## Repository settings

GitHub secret scanning, push protection and dependency vulnerability alerts are enabled. Merged branches are deleted automatically. Main requires the publication check for ordinary changes and disallows force pushes and deletion; repository administrators retain their normal bypass ability. The description, homepage and topics match `release/github.json`; the README describes the implemented local app, bounded evidence collection, evaluation limits and relationship to Filing Digest. A read-only check of Filing Digest confirmed the README responsibility boundary; no partner files were changed.

The full application verification and deployment evidence remain in the [architecture audit](2026-09-08-architecture/README.md).
