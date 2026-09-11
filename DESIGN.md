# Filing Agent design direction

Status: September 11, 2026. Owner selected **B: Ledger** from three rendered static alternatives, then extended it with responsive continuity for the Filing Agent application and replay. The Ledger hierarchy and evidence semantics remain the identity. [ADR 0012](docs/adr/0012-responsive-continuity-for-reading.md) records the interaction decisions.

Design for a filing reader investigating company disclosures in Korean or English on desktop and mobile. The experience should feel calm and support sustained reading: warm neutral backgrounds, readable typography in both languages, restrained color, and prominent financial figures and original-filing sources.

Use Ledger's paired reported figures, subordinate calculated change, ruled figure rows, and tabular source fragment. Retain its warm neutrals, restrained evidence accent, Pretendard and tabular numerals as the implementation baseline. The relationship to Digest is expressed through the neutral research-workspace character and project story; an identical font family is not a requirement. Desktop evidence opens beside the conversation at approximately 45% width.

Put language and theme controls directly in the top bar beside New investigation and History. Use visible native-language names `한국어 / English` with an explicit selected state and a separate sun/moon theme button with an accessible destination label. Do not hide these controls in an overflow menu. On narrow screens, give controls a deliberate second row rather than hiding or crowding them.

Mobile evidence has one full-height view with a visible close button, independently scrollable content, safe-area padding, Escape support and focus return to the selected figure. No peek detent, drag handle, or drag-to-resize in v1. Mobile replay starts with the conversation visible; tapping a figure opens evidence. Desktop replay still opens its first source automatically. Preserve the conversation's position when evidence closes. Modal focus containment applies to mobile evidence; desktop evidence remains nonmodal.

Responsive continuity is the interaction standard. Controls acknowledge press immediately. Evidence and modal surfaces use critically damped springs that can retarget from their current presentation when the reader closes or reopens them. A surface enters from the direction of its triggering control and returns along the same path. New input remains available while an exit settles. Motion explains source, destination and hierarchy; it never delays an action or runs decoratively. Reduced motion replaces spatial travel with a near-immediate opacity change, reduced transparency uses solid chrome, and increased contrast strengthens surface boundaries.

Support light and dark themes, initially following the system preference, with an explicit switch. Verify both themes equally in Korean and English. The calm, warm direction applies to both.

Default to a concise answer and key figures with expandable explanation and evidence. The local application's entry view exposes supported companies, periods, and example questions alongside a free-form prompt. Editing an earlier question prefills a new investigation; conversation branching is deferred. Changing language updates controls and future answers while preserving earlier answer text. Public replay language controls use deliberately prepared recorded content rather than live translation or inference.

[ADR 0006](docs/adr/0006-persisted-local-workflows-and-release-scope.md) records the implemented release scope; the [release audit](docs/audits/2026-09-08-slice/README.md) records its verification.

Apply antislop during design and implementation as configured in AGENTS.md. Use this brief as the visual direction; document the reasons for major design choices and verify the eventual interface across languages, screen sizes, keyboard navigation, and loading, empty, partial, and error states.

Design dials: ENERGY 1, RHYTHM 2, MOTION 2. Paired reported figures establish the primary comparison; the shared figure/excerpt highlight identifies the selected evidence. Numeric alignment supports comparison, visible controls improve discoverability, and the single mobile evidence state reserves the full reading area for the source.

Major decisions and reasons:

- Warm neutral surfaces keep long filing excerpts calm; brown remains the one evidence accent because it already identifies source selection.
- Pretendard stays because its Korean and Latin readability is proven in the existing bilingual application.
- Conversation and evidence remain a 55/45 desktop split because the relationship is parallel reading, while mobile gives evidence the full viewport for legibility.
- Header and composer use the only translucent materials because they float above scrolling content; evidence and dialogs stay solid for sustained reading.
- Soft elevation belongs only to evidence and modal surfaces because those are the layers that move above the conversation.
- Springs are critically damped because motion should communicate continuity without bounce or flourish.
- Native scrolling, disclosure controls, form behavior and keyboard order remain because familiar platform behavior is more direct and accessible than custom gestures here.

Use the Filing family’s bracketed F mark in the header and favicon to make the relationship to Filing Digest visible. Keep Agent’s brown evidence accent, ruled rows, and dense ledger workspace so the two products remain distinct at a glance.
