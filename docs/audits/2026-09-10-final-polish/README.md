# Final user-flow and presentation polish

Work started September 10 and was verified September 11, 2026. This record covers
the bounded final-polish changes, not a new claim of general financial-language
accuracy or production multi-user security.

## Changes

Explicit company requests retain all meaningful question text when checking the
supported grammar. An unsupported company or scope cannot be silently dropped
just because the model returned a recognized company. Unresolved requests ask for
clarification without presenting a narrower financial report. This conservative
policy can ask for clarification on unfamiliar phrasing; it is not unrestricted
entity recognition. [Decision](../../adr/0011-clarify-unhandled-company-pairs.md).

Starter questions follow the interface language. A separate example explains
what happens outside the verified collection. Saved investigations keep their
original result; continuing is the primary action and a new investigation with
current approved data does not download filings. The shared Filing mark identifies
the family while the Agent workspace retains its own typography and layout.

The public first investigation now starts with a Samsung FY2023 revenue question
and continues with a natural FY2022 comparison. The original-filing excerpt and
calculated change remain inspectable. The engineering page places the real
application recording before implementation details. Historical evaluation counts
remain tied to the earlier release rather than being relabeled as new results.

## Recorded behavior

The new browser recording uses actual local inference, source inspection, saving,
reopening and continuing. Captions describe visible actions in Korean and English;
they do not translate the regulator's original excerpts. The recording JSON
records capture time and completed turn identifiers. Sanitized replay data contains the displayed answers; raw model diagnostics remain local. Original financial values remain in the
verified historical snapshot.

Verification results and the exact static-artifact manifest accompany the final
release. The source ZIP is built from the explicit source allowlist; private
history, backups, raw model diagnostics and planning are excluded.

## Verification scope

The real-model gate uses one fresh held-out trial: 20 Korean and 20 English
scenarios. This is a bounded regression check, not a replacement for or extension
of the historical three-trial evaluation. Additional live cases exercise mixed
supported/unsupported companies and the localized starter questions.

Browser checks cover saved reload, continuation, clarification recovery, original
source inspection, Korean/English, light/dark themes, keyboard focus, and 320/390
pixel layouts. Controlled failure tests separately exercise late responses and
storage recovery. Automated axe checks supplement actual screenshot inspection;
they do not establish comprehensive accessibility conformance.

The public replay contains three actual investigations, including the two-turn
Samsung comparison, a company change, and an unavailable-metric response. It
makes no live inference requests. Project-note links, video playback and captions
are checked separately. Financial excerpts retain their original language.

The presentation review retained the Ledger design, shared family mark and
separate Agent workspace. It checked copy and headline punctuation, keyboard and
focus behavior, responsive reflow, and visible loading/error/recovery states.
No new decorative visual system or general-chat capability was introduced.

No database schema or production data change is part of this release. Original
local investigations are checked against a pre-work content-hash baseline.

## Results

- 57 policy tests and 19 application tests passed
- Fresh held-out model trial: Korean 20/20 and English 20/20 passed
- Eight additional live scope and starter cases passed
- Live UI, static replay, failure recovery, responsive and project-note browser checks passed
- Both caption tracks loaded and the actual video played in the browser
- Source archive manifest verified; 57 tests passed from the extracted archive
- All 92 pre-existing local investigations retained identical content hashes

[Machine-readable results](verification.json) record source hashes and scoped checks.
[Artifact manifest](artifact.json) pins the exact deployable static files.
