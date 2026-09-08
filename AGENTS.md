# Filing Agent

Current phase: implementation and verified static replay release. README.md
indexes the application, release evidence, and historical planning. FOUNDATION.md is historical context;
its build-start prompt and superseded assumptions are not current instructions.

Filing Digest is the partner project. Inspect it read-only and keep
this project's changes within filing-agent.

## Agent skills

### Issue tracker

Specs and tickets live in GitHub Issues. Before tracker operations,
read docs/agents/issue-tracker.md.

### Triage labels

Use the five canonical triage labels. Before labeling issues,
read docs/agents/triage-labels.md.

### Domain docs

Use one root CONTEXT.md and docs/adr/. Before domain exploration
or design, read docs/agents/domain.md.

<!-- antislop:start -->
## antislop

Apply the installed `antislop` skill during planning and implementation.
Read its core at `~/.agents/skills/antislop/SKILL.md` before writing
product copy, code comments, or UI; use task-specific companion skills
when relevant and available.

The owner selected DURING mode and authorized this integration.
Reuse that choice across sessions; setup and mode confirmation are complete.
Before UI work, read DESIGN.md or the owner's explicit visual direction.
If direction is missing, resolve it with the owner before designing.
Apply the skill's UI delivery checks when a UI is part of the deliverable.
<!-- antislop:end -->
