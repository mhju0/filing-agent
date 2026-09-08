# Documentation

Start with the [project overview](../README.md) for Filing Agent's purpose, its relationship to Filing Digest, and the public replay.

## Current guides

| Document | Use it to |
|---|---|
| [Operating guide](../slice/README.md) | Install and run the local app; manage investigations, backups and replay exports |
| [Design direction](../DESIGN.md) | Understand the approved interface and interaction requirements |
| [Domain glossary](../CONTEXT.md) | Look up shared terms and evidence boundaries |
| [Architecture decisions](adr/README.md) | Follow the decisions, alternatives and later refinements |
| [Model experiments](../bench/README.md) | Reproduce the benchmark and inspect the model-selection evidence |
| [Evaluations](../evals/README.md) · [results](../evals/RESULTS.md) | Run conversation scenarios and read the measured outcomes and limits |
| [Release guide](../release/README.md) | Prepare the public source archive and deploy the verified static replay |
| [Verification records](audits/README.md) | Inspect filing coverage, application checks and release evidence |

## Design studies

[Rendered alternatives](../design/alternatives/README.md) preserve the interface studies, selection notes and prototype verification. Current implementation guidance lives in DESIGN.md and the architecture decisions.

## Repository instructions

[AGENTS.md](../AGENTS.md) is the entry point for coding agents. Supporting instructions cover [domain documentation](agents/domain.md), the [issue tracker](agents/issue-tracker.md) and [triage labels](agents/triage-labels.md).

## Where documents belong

Keep the project overview, agent entry point, glossary and design direction at the repository root. Keep operating instructions beside their component. Record consequential decisions in `docs/adr/`, verification with its evidence in `docs/audits/`, with each report. Personal research and planning stay in ignored local directories.

Private planning and recruiting research are excluded from Git and the public source archive. Its contents are controlled by the [release allowlist](../release/source_bundle.py).
