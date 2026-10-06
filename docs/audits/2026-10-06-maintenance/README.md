# Portfolio maintenance closeout · 2026-10-06

The owner approved closing feature development and publishing a dated baseline.
The runtime, approved facts and captured results are unchanged. Maintenance
covers defect/security fixes and accurate documentation; new features require
owner reopening. See [policy](../../MAINTENANCE.md).

## Changes

- Added maintenance status, scope and interview operating guidance.
- Fixed the Korean Overview coverage-table overflow below 420px with two padding
  declarations. No financial arithmetic or persistence behavior changed.
- Preserved static replay and qualified model boundaries. Private recruiting
  review and ownership questions remain outside the public repository.

## Verification

Nine frontend tests and the TypeScript/Vite build pass. The Overview browser
matrix covers Korean/English, light/dark and 320/390/1440px: no document overflow,
axe violations or page/console errors. Korean 320px table right edge is now 304px.
Historical live-model and source qualification are not rerun by this closeout.
Physical-device and full VoiceOver checks remain unestablished.

[artifact.json](artifact.json) records the assembled static file allowlist/hashes.
Deployment and protected CI results are recorded in the GitHub release and private
closeout record after verification. Original recordings remain byte-identical.
