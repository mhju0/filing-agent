# Issue tracker: GitHub

Specs and tickets live in mhju0/filing-agent GitHub Issues.
Use the gh CLI from this checkout.

## Operations

- Read: gh issue view <number> --comments.
- List: gh issue list with appropriate state and label filters.
- Create: gh issue create --title "..." --body-file <file>.
- Update descriptions: gh issue edit <number> --body-file <file>.
- Apply/remove labels: gh issue edit --add-label / --remove-label.
- Preserve multiline text using a body file.
- Follow the active skill's review and publication steps.

## Dependencies

Use native GitHub blocking relationships when available.
Otherwise record "Blocked by: #<number>" in the ticket body.
A ticket is available when all its blockers are closed.

## Wayfinding

Use one map issue with linked decision tickets.
Prefer native sub-issues; otherwise use a task list on the map
and a "Part of #<map>" reference on each child.

## Pull requests as a triage surface

PRs as a request surface: no.
