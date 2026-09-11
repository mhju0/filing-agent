# Responsive continuity

This release applies the owner's responsive-continuity direction to the Filing
Agent live application and static replay. Filing Digest is unchanged.

The interface retains the reported figures, source excerpts, original-filing
links and conversation semantics. Warm reading surfaces and restrained evidence
emphasis remain; controls and temporary layers share a quieter visual system.
Motion explains the relationship between a selected figure and its evidence.
Closing a temporary layer returns control immediately. Reduced motion removes
spatial travel, and reduced transparency uses solid surfaces.

The implementation decision is recorded in
[ADR 0012](../../adr/0012-responsive-continuity-for-reading.md).

## Verification scope

Verification covers the live interface and the static replay separately. The
recorded financial conversations remain authentic historical executions; this
presentation release does not rerun or relabel the financial-language benchmark.
The project-notes video remains the September 10 final-polish recording, showing
the earlier presentation. The interactive replay uses the current interface.

Normal-motion checks exercise interruption, reopening, evidence changes and
responsive layout changes. Reduced-motion, keyboard, focus, language, theme and
small-screen checks supplement the existing conversation-state regressions.
Automated accessibility checks do not establish comprehensive screen-reader or
physical-device conformance.

## Results

- 57 policy tests and 19 application tests passed. Backend financial and storage
  code is unchanged.
- The complete live browser flow passed: examples, actual inference, figures and
  formulas, save/reopen/continue, clarification, drafts, History, confirmation and
  deletion. Only test-created investigations were deleted.
- Late-response and storage-recovery regressions passed, including closing History
  while its request is pending and reopening it deliberately.
- Normal-motion checks passed in Chromium, including measured midflight reversal,
  focus acquisition on rapid reopen, and desktop/mobile/desktop grid recovery.
  WebKit passed the targeted mobile evidence open/Escape check.
- Reduced motion at startup and midflight passed. Open evidence is opaque, theme
  colors update without a transition, and 200% text reflows at 320px.
- Korean/English, light/dark and 1440/390/320px browser checks passed automated axe
  checks. The lowest checked core text contrast is 5.38:1.
- All 92 original local investigations retained identical content hashes.
- The assembled static replay passed the full replay suite and normal-motion
  checks under its content security policy, with no live API or foreign requests.
- Project-note links, captions and video playback passed. The source archive
  matches the current UI files and all of its recorded manifest hashes.
- Production checking found a one-pixel table overflow with the bundled font
  unavailable at 200% text on a 320px screen. Fixed table sizing and wrapping
  preserve readable values without clipping. The regression now blocks the font
  and checks fallback text before and after font loading settles, on desktop and
  mobile. The full replay and Chromium/WebKit continuity checks passed again.

Physical iPhone touch behavior and a full VoiceOver session have not been verified.
The WebKit check does not replace the wider Chromium live-flow coverage.

[Machine-readable verification](verification.json) records the scoped checks.
[Artifact manifest](artifact.json) identifies the reviewed static release.
[Design delivery checks](design-gate.md) record the applied design gates.
