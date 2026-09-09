# Interpret bounded follow-ups against the active investigation

Date: 2026-09-10. The first owner walkthrough exposed a broken follow-up:
“2022년과 비교하면 얼마나 증가하거나 감소했어?” lost Samsung context after a
successful FY2023 revenue answer. The prior maintenance qualification did not
establish natural-language usability.

Retain the conservative company-free financial vocabulary boundary, including
unknown-company and exclusion rejection. Extend it to common comparison clauses
and relative fiscal-year references. Within that boundary, code carries unchanged
company and metric context even when the model omits them. A conflicting nonempty
model company still fails rather than silently switching evidence.

A comparison with one explicit year and one selected context year uses both.
A year-over-year comparison with one selected year uses that year and its prior
year. A relative-year lookup uses the prior selected fiscal year, never the machine
calendar. Without a unique context year, a relative lookup requests a year instead
of guessing. These are bounded interpretation rules, not unrestricted conversation
or automatic filing updates.

Clarification asks only for missing fields. Missing-period replies list available
snapshot years for the selected company and metric. Comparison wording includes
the code-calculated percentage. Saved-investigation guidance explains continuation
and makes clear that refreshing does not download filings. Historical saved
answers and public recordings are not rewritten.

Verification includes the owner's exact wording, natural Korean/English variants,
relative references, missing model context, unknown companies, existing policy and
storage tests, real local model requests and browser workflows. First-use feedback
remains part of qualification; test counts alone do not establish usability.
