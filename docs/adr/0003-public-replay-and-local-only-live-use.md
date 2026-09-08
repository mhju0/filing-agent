# Public replay and local-only live use

The owner chose a public demonstration for viewers and real application execution only on their personal Mac, explicitly removing online invitations and remote live sessions. The public artifact remains a clearly labeled interactive replay of captured investigations; the Mac runs the actual application, local inference, databases, and isolated Digest dependency.

This supersedes remote invitation, sign-in, revocation, multi-user account, and hosted live-dependency requirements from earlier interview rounds and narrows ADR 0002's authentication/exposure scope. No account system, email delivery, tunnel, or continuously available live server is required. Local conversation isolation, saved evidence, retention/deletion, source verification, and the approved bilingual quality targets remain; evaluation cases for remote accounts are replaced with local isolation, replay separation, and persistence cases.

The public replay must work without connecting to the owner's Mac, model runtime, or private data. Publishing the static artifact is separate from running the application; remote live access can be reconsidered only as a future scope decision.

Local execution keeps infrastructure and model dependencies under the owner's control. A static replay lets visitors inspect the workflow without arranging access to the Mac. This scope leaves multi-user isolation and public-service operations unproven.

The replay must show authentic captured execution, label recorded playback clearly, support Korean and English, and expose the evidence behind each figure. The local application must remain reproducible for technical review. [ADR 0006](0006-persisted-local-workflows-and-release-scope.md) and the [release audit](../audits/2026-09-08-slice/README.md) record the implementation and verification of these requirements.
