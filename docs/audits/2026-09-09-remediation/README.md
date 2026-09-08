# Approved remediation · 2026-09-09

The owner approved the [joint audit's completion sequence](../2026-09-09-release-readiness/README.md)
and requested company expansion. This record follows that audit; it does not
retroactively turn its failed checks into passes.

## Filing Digest

Ten companies were qualified in isolation and added to the working corpus:
Kia, Samsung SDI, LG Chem, LG Electronics, Samsung Biologics, Costco, Amazon,
Alphabet, Meta and Walmart. The corpus now has 18 companies, 23 filings,
153 financial records and 2,057 indexed chunks. Original row fingerprints are
unchanged, and a PostgreSQL 16 backup passed a restore test before promotion.
See the [coverage report](https://github.com/mhju0/filing-digest/blob/main/docs/COVERAGE.md).

Generic parser repairs cover dash-separated SEC headings, heading-only tables,
inline Item cross-references and doubled DART attribute quotes. Financial prose
checks reject all five audit expressions while preserving structured figures.
Loopback port binding, HTTP host validation, a qualified dependency lock and
legacy-migration tests address the other technical release findings.

Verification passed 436 offline tests (21 intentional skips), 21 isolated
PostgreSQL tests, 36 native unit tests and three native UI flows. A repeated
native contrast-audit failure was fixed by increasing muted-text contrast.
The new large-text and accessibility checks pass. Fresh and working Python
environments report no known dependency vulnerabilities.

Bilingual retrieval passed for all ten additions. Targeted Solar generation
runs exposed wrong-language prose and correctly blocked financial expressions.
Prompt language handling was corrected and mixed-company-name cases added to
regression tests. These runs are not a replacement for the earlier full quality
evaluation. Language inference is heuristic; financial-expression guards do not
prove every sentence is entailed by its source.

## Filing Agent

Simple Korean/English company corrections now select the stated company.
Ambiguous corrections and unsupported names with existing context clarify
instead of silently substituting a supported company. Company continuity is
accepted only for bounded company-free follow-ups; unfamiliar phrasing may
require the user to name a supported company again.

The 39 benchmark/policy tests and 17 application tests pass. Six targeted live
local-model cases and the live browser workflow were rechecked. Review then
added contextual unknown-company and ambiguous-correction regressions. The
separately qualified snapshot and recorded investigations are unchanged.
Application tests and the web build now run in CI beside the publication guard.
The downloadable source archive is rebuilt from the current application source.

## Review and remaining limits

The code-review skill's independent Standards and Spec reviews found three
substantive issues: mixed-name language selection, unsupported-name context
inheritance, and overly permissive corrections. Each received a fix and
regression coverage. A contradictory test comment was removed. Release prose
received one humanizer pass to keep claims specific and measured.

Physical-device VoiceOver, every native screen/text-size combination and a full
fresh installation on another Mac remain unverified. GitHub's previously cached
private-history support request still needs owner submission; another history
rewrite is not a remedy. The prepared request is kept private. Neither app adds
accounts, public live inference or automatic ingestion.

[Machine-readable evidence](evidence.json) records counts and restore hashes.
