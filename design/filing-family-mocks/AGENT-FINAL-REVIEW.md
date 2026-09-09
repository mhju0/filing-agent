# Consolidated Agent proposal, September 9

Owner approved the rendered direction and requested a pull request on September 9.

Local review: http://localhost:4178/agent-final.html?lang=ko&v=1

This proposal combines the entry screen, recorded investigation, and shared F
icon direction. It does not replace the local application, public replay, or
installed icons. The original five studies remain available as comparison evidence.

## Decisions

ENERGY 1 / RHYTHM 2 / MOTION 1, following the owner's calm Filing family direction.

- Paper and ink backgrounds connect Agent to Digest without competing with evidence.
- ExtraBold Nanum Myeongjo gives the entry invitation the approved Digest character.
- Pretendard investigation headings and tabular figures preserve Agent's Ledger identity.
- Blue identifies evidence selection; the selected row also has a pressed state and weight change.
- Reported values lead; the calculated percentage remains subordinate.
- Desktop evidence updates beside the answer; mobile uses one full-height modal.
- The existing F remains recognizable, with a small blue open corner distinguishing Agent.
- Service names remain visible because small icon details alone are insufficient identification.
- Headline phrases omit periods. Actual recorded answers and original filing titles retain punctuation.

## Delivery checks

PASS, hard gate: Chrome rendered the entry, all three actual recordings, and icon
pair. Korean/English entry and icons passed 320px overflow checks in both themes
(305px client/scroll width after scrollbar). Korean light and English dark replay
and source views were also checked at 320px. No broken images were observed.
Original values, source identities, and timings come from the existing recording.
Empty/loading/error branches are present in source; network fault injection was
not performed for this visual review.

PASS, purpose gate: typography, ruled figures, evidence accent, mobile modal and
icon variation each serve the decisions above. No decorative charts, statistics,
testimonials, or new product capabilities were introduced.

PASS, liveliness: entry invitation, investigation figures and icon pair each have
one focal point. The entry has reading space; the investigation has denser ruled
rows. The shared F and blue evidence selection identify the service. Motion is
limited to ordinary interaction feedback.

PASS, craftsmanship: the following controls were exercised in Chrome:

- All three entry examples open their corresponding recording.
- Start/replay controls switch views; Enter also activates the replay control.
- Annual comparison, company switch and missing evidence select their recorded result.
- Previous/next question switches Samsung and NAVER within the company scenario.
- Desktop FY2023 selection updates the source table to 258,935,494 million KRW.
- NAVER source retains its original KRW unit and 9,670,643,576,585 amount.
- Mobile figure selection opens the source; Close and Escape dismiss it.
- Escape returns focus to the selected FY2023 figure.
- Calculation and first-use disclosures expand their actual text.
- Icon navigation and return navigation open the corresponding pages.
- Korean/English and light/dark controls update the visible content and styling.
- Rendered DOM-color contrast checks found no below-threshold text in entry and
  icon pages across both languages/themes, or in the checked English dark replay.
- Korean entry heading reports font weight 800; no headline terminal periods.
- Chrome console reported no errors or warnings; JavaScript syntax and Git whitespace checks pass.

Source links retain exact DART filing URLs from the recorded data. External DART
availability was not retested in this visual review. This is a targeted review,
not a whole-app accessibility or runtime release qualification.

## Background cleanup

Stopped the obsolete Digest preview (4179), idle Agent runtime (8765), and its
PostgreSQL instance at `.local/slice-postgres`. Kept the review server (4178).
The pre-existing Ollama service was left running because it is shared outside
this preview task.
