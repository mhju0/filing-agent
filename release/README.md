# Static release assembly

This directory holds release-building scripts, not a copy of private planning. Only the generated `slice/replay` directory is eligible for static deployment. That directory must be inspected before deployment and must contain no database files, environment files, personal research, private history or raw model diagnostics.

The application source distribution is assembled from an explicit allowlist. It is a fresh archive with no `.git` history. The private `mhju0/filing-agent` repository is not made public.

Production: https://filing-agent.vercel.app. Deploy only with `./release/deploy.sh` after rebuilding and reviewing the artifact. It verifies the exact file allowlist and hashes, then changes into the static directory before invoking Vercel. The repository root excludes all files through `.vercelignore`. Git-triggered deployments are disconnected; keep the private repository and hosting separate.
