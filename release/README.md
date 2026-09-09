# Static release assembly

This directory holds release-building scripts, not a copy of private planning. The reviewed `slice/replay-release` directory is the current static deployment artifact. That directory must be inspected before deployment and must contain no database files, environment files, personal research, private history or raw model diagnostics.

The application source distribution is assembled from an explicit allowlist. It is a fresh archive with no `.git` history. The GitHub repository is public. Private planning and recruiting research are ignored locally and excluded from published history and source archives.

Production: https://filing-agent.vercel.app. Deploy only with `./release/deploy.sh` after rebuilding and reviewing the artifact. It verifies the exact file allowlist and hashes, then changes into the static directory before invoking Vercel. The repository root excludes all files through `.vercelignore`. Git-triggered deployments are disconnected; keep repository publication decisions and hosting separate.

`github.json` records the English GitHub description, homepage and topics. Keep the sister-project link consistent with the root README, operating guide and public project notes.

The current artifact manifest is `docs/audits/2026-09-10-natural-flow/artifact.json`. `RELEASE_AUDIT` can select a different reviewed manifest; the deployment script still requires the exact static release directory and file hashes.

Before publishing repository changes, run `python3 release/check_publication.py`. It checks tracked files against the ignore rules and rejects Markdown links to local-only material. GitHub also runs this check on pull requests and main. Run `gitleaks git . --config .gitleaks.toml --redact` for a local history scan when Gitleaks is installed; the configuration only exempts public filing-response SHA-256 fields.
