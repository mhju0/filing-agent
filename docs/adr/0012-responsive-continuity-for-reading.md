# Use interruptible continuity for reading surfaces

Date: 2026-09-11.

## Decision

Filing Agent keeps the Ledger information hierarchy and adds responsive continuity to the local application and public replay. Evidence, history and confirmation surfaces open from the direction of their triggering control with critically damped spring motion. Closing retargets the same surface toward its source, and a new open request may reverse an exit from its current presentation. The underlying action takes effect immediately; settling motion does not lock input.

Controls acknowledge pointer down through a small press response. Existing browser scrolling, disclosure, form and keyboard behavior remain native. No drag-only gesture, detent, decorative animation or artificial delay is added.

The evidence selection and its source panel remain a single relationship. Desktop keeps evidence nonmodal beside the conversation. Mobile keeps one modal, full-height evidence surface. The selected evidence and evidence reading position survive the 850px layout boundary, and closing restores focus without moving the conversation.

Reduced motion removes spatial travel and uses a near-immediate opacity change. Reduced transparency makes the header and composer solid. Increased contrast strengthens surface boundaries. Light and dark themes, Korean and English content, replay and live investigation state use the same presentation behavior.

## Reasons

- Critically damped springs provide a physical settle without decorative bounce.
- Keeping an exiting surface present but inert allows visual continuity while releasing modality and input immediately.
- Direction from the trigger and a symmetric return preserve spatial context between a reported figure and its original filing evidence.
- Native scrolling and controls retain platform familiarity, keyboard behavior and user settings.
- Two translucent chrome surfaces distinguish persistent navigation and composition from solid reading surfaces without flattening every layer into glass.

## Consequences

The frontend includes a motion runtime and must verify normal-motion interruption as well as reduced motion. Tests that inspect dialogs must distinguish the active semantic dialog from an inert exiting visual surface. Static replay security remains unchanged because motion is bundled locally and makes no network request.

This decision supersedes ADR 0004 and the earlier DESIGN.md statement that evidence transitions are immediate. It does not change filing evidence, lifecycle, persistence, cancellation, source navigation or the boundary between live and replay state.
