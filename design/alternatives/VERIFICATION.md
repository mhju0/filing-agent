# Static alternative verification

Scope: the three owner-requested static investigation screens. These checks do not establish application, model, retrieval, persistence, cancellation, or production-security behavior.

## Browser evidence

`npm run build` produces all three pages plus the default A entry. `npm run verify` launches local Google Chrome against the production preview, records its actual version in `verification.json`, and captures the pages under `screenshots/`.

The script exercises figure selection, both calculation operands, retained keyboard focus, evidence closing/reopening, original-language excerpts and labeled translations, expandable explanation, History, New investigation's prototype draft, context explanation, retained draft on unsupported submission, IME-safe Enter handling, working language/theme controls, bottom-sheet expansion/collapse/drag/Escape, and return to the composer. The A/B/C links are ordinary page links and were also inspected with agent-browser.

Automated axe checks cover Korean and English in both desktop themes, Korean mobile peek, and English/dark expanded mobile evidence. Responsive checks cover 375, 390, 768, 1024, and 1280px; reference desktops use 1440px. The test browser uses reduced motion. Runtime screenshots and checks are from actual browser renders, not drawn mock screenshots.

## Antislop delivery gate

| Gate | Status and evidence |
| --- | --- |
| Hard gate: responsive content and truthful copy | PASS: no document overflow at tested widths; figures come from the fixture; static labels and unmeasured timing prevent false live-execution claims. |
| Hard gate: genuine controls and destinations | PASS: visible controls perform the documented local actions; original-report links use the fixture URL; no sign-in, live invitation, or dead model controls appear. |
| Hard gate: keyboard, focus and accessible states | PASS: keyboard formula/source flow, focus return, mobile trap/Escape and inline error are checked; axe reports no violations in the audited states. |
| Hard gate: themes and build verification | PASS: both themes and languages render in Chrome; production build and interaction checks complete; report records console errors and external requests. |
| Purpose gate | PASS: figure emphasis differs by requested composition; card boundaries in C are owner-directed; one accent denotes selected evidence; shadows denote elevated sheets/dialogs. |
| Liveliness gate | PASS: dials and focal points are declared in README; evidence highlights provide a consistent identity motif; spacing separates question, answer, calculation and original source. |
| Craftsmanship and consistency | PASS: original values/units survive formatting; selected figure and source stay synchronized; mobile switches to a sheet; no default charts, fake testimonials, marketing sections or endless animations. |

Computed contrast using the installed Antislop checker:

| Pair | Ratio | Normal text |
| --- | ---: | --- |
| Light muted `#6b655b` / paper `#f7f4ee` | 5.26:1 | PASS |
| Dark muted `#b7aea0` / surface `#2a2824` | 6.71:1 | PASS |
| Light accent `#87482e` / selection `#f1e2d5` | 5.53:1 | PASS |
| Dark accent `#edb28e` / selection `#48362a` | 6.19:1 | PASS |

## Review corrections

| Before | After | Why |
| --- | --- | --- |
| Locally declared render components could remount controls during state changes. | Stateless render helpers preserve the underlying control identity. | Formula toggling and source selection must not discard keyboard focus. |
| Escape was handled only inside the mobile panel. | While the modal sheet is open, document-level handling preserves Escape and tab containment after a pointer drag. | Dragging can move focus outside the sheet's descendants. |
| English amounts used `T KRW`. | English amounts spell out `trillion KRW`, with a secondary unit line in figure controls. | Explicit units follow the brief and fit bilingual layouts more clearly. |
| The first desktop capture cropped lower sections in B/C. | Shared 1440 × 1200 reference captures include the complete illustrative trail. | Comparisons should expose the same requested elements. |

## Limits

No physical phone/software-keyboard test, VoiceOver session, Safari-specific review, full 200% zoom audit, or live DART deep-link validation was performed. Responsive browser checks and axe do not replace those release checks. External requests are blocked during capture; deliberate navigation to the linked original PDF is separate from the application's asset loading.

The narrow screenshots illustrate peek state, which intentionally reveals only the beginning of scrollable evidence. Expand or scroll for metadata, conversion, original link and limitations. Prototype-only controls explain their scope instead of simulating a production backend.

Before production implementation, several engineering assertions in the supplied decision record require exact contracts: checkpoints do not alone stop an inference process; a retry's idempotency key must distinguish reattaching to an existing run from a new attempt; untranslated fallback text must not be labeled as a translation; and source-code grepping alone cannot establish absence of runtime network traffic. These are implementation qualifications, not changes to the selected visual alternatives.
