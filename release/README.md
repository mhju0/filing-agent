# Static release assembly

This directory holds release-building scripts, not a copy of private planning. The reviewed `slice/replay-release` directory is the current static deployment artifact. That directory must be inspected before deployment and must contain no database files, environment files, personal research, private history or raw model diagnostics.

The application source distribution is assembled from an explicit allowlist. It is a fresh archive with no `.git` history. The private `mhju0/filing-agent` repository is not made public.

Production: https://filing-agent.vercel.app. Deploy only with `./release/deploy.sh` after rebuilding and reviewing the artifact. It verifies the exact file allowlist and hashes, then changes into the static directory before invoking Vercel. The repository root excludes all files through `.vercelignore`. Git-triggered deployments are disconnected; keep the private repository and hosting separate.

`github.json` records the English GitHub description, homepage and topics. Keep the sister-project link consistent with the root README, operating guide and public project notes.
