# Contact and privacy release · 2026-10-06

This static replay release adds bilingual email support, a public GitHub Issues link and an expandable privacy/contact disclosure. The Filing Digest description now says source-linked summaries and Q&A. It publishes source commit `4875046` without changing local inference, persistence or recorded results.

[artifact.json](artifact.json) records the exact 27-file allowlist and SHA-256 hashes checked by `release/deploy.sh`. `recording.json` is byte-identical to the previous release (`8bf71eae94cd9c72f04f779b90534dddf3d81baadebf3f5665b40d70a5123b0f`). The fresh application source archive contains 78 entries from the existing explicit allowlist; its embedded hashes match every included source file. No environment files, private planning or Git history are included.

Verification before publication:

- Nine format/glossary tests and the TypeScript/Vite production build pass.
- Publication boundary checker passes; Gitleaks scans 49 commits with no leaks found.
- Assembled footer passes keyboard disclosure toggling, bounds, axe WCAG A/AA checks, page-error and static-request checks in Korean/English, light/dark and 320/390/1440px.
- Existing release-material checks pass for project-note links, video/captions, reflow and axe at 320/390/1440px. The old harness expects recording errors on the Overview; the current Recorded runs route is checked separately for visible failure and working reload.
- The previously recorded Korean Overview coverage-table overflow at 320px remains outside this bounded footer change. Physical-device and full VoiceOver verification are not established.

Historical model evaluation and project-note evidence remain linked to the [2026-09-10 verification record](../2026-09-10-final-polish/README.md). The older release manifests remain unchanged.
