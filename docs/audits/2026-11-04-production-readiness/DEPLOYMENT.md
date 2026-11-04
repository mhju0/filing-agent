# Production release verification · 2026-11-04

[Verified] **Deployed and verified:** [Filing Agent](https://filing-agent.vercel.app), deployment `dpl_36PrV9fxFmnYhte95tkvfD1sj9eT`, application commit `67643a50da45e080f36a1febab4b4cf9d092ed61`.

This closes the [maintenance audit](README.md). The public product remains a static replay; local API, model and PostgreSQL verification are recorded separately in that audit.

## Release and CI

[Verified] [PR #26](https://github.com/mhju0/filing-agent/pull/26) merged after its Publication boundary and Application regression checks passed. [PR CI](https://github.com/mhju0/filing-agent/actions/runs/41755210729) and [merged-main CI](https://github.com/mhju0/filing-agent/actions/runs/41755441452) both succeeded. Local acceptance included 53 application, 57 policy, 9 frontend and 2 release tests, plus the connected browser/model/database flows.

[Verified] Independent reviewers accepted the exact code candidate `890599c` and final release candidate `3131e38`. The final review checked every artifact hash, all source ZIP payloads against committed source, private-path exclusions and the unchanged deployment target.

[Verified] Deployment used only:

```sh
RELEASE_AUDIT=docs/audits/2026-11-04-production-readiness/artifact.json ./release/deploy.sh
```

The pinned Vercel CLI was 59.11.7. Vercel returned READY, the canonical alias resolved to the new deployment, and deployment metadata identified the intended `filing-agent` project and merged application commit. Git-triggered deployment remains disconnected.

## Production readback

[Verified] All **26 public files** returned HTTP 200 and matched the committed SHA-256 hashes, including both fonts, application JS/CSS, original recordings/media, source ZIP and verification materials. The twenty-seventh artifact input, `vercel.json`, returns public HTTP 404. Its bytes were retrieved through the authenticated deployment-source API and matched the manifest; its cache/security rules were verified in public responses. It is a deployment input, separate from the public outputs.

[Verified] HTML, recording/ledger JSON and source ZIP retain revalidation. Only the four content-hashed assets use `public, max-age=31536000, immutable`. CSP, `nosniff`, `no-referrer`, Permissions Policy and platform HSTS remain present. Anonymous `/api/session`, `/api/investigations`, `.env` and `.git/config` probes returned 404; a POST to `/api/investigations` also returned 404. No production data was created or modified.

[Verified] The actual public deployment passed:

- 64 rendered surface checks: both languages/themes, desktop and touch/mobile, all four surfaces at 200% text, Korean word boundaries, zero document overflow and axe violations.
- Replay scenario/turn navigation, source/formula controls, withholding, keyboard focus, mobile evidence, Escape and reduced motion.
- Evidence close/reopen interruption, explicitly in-flight and settled breakpoint handoffs retaining scroll position, font failure, and automated WebKit mobile evidence.
- Six engineering-note variants, video/captions and material links.
- Controlled recording failures and delayed responses: repeated 503 retry, recovery to a deep-linked turn, and Home card scenarios 1/2 under failed or pending loading. These use browser-controlled failure responses on the real production UI; they do not claim an observed production outage.

[Verified] In three actual production navigations within one fresh Chrome context, the two returning visits changed from **four versioned-asset requests / 1,200 transfer bytes each** before release to **zero requests / zero transfer bytes each** after release. HTML and mutable data still revalidate. This establishes the intended browser-cache effect, not a claim of faster cold rendering or an uptime/capacity result.

[Verified] A separate independent production spot-check confirmed the canonical alias/commit, eight public file hashes including every hashed asset and the source ZIP, security/cache headers, source archive integrity, absence of a public live API and availability of the previous rollback deployment. The full 26-file/configuration readback, browser matrix and warm-cache measurements were root-verified.

## Rollback and cleanup

[Verified] Previous deployment `dpl_8HUwQ73gH9yrGhyJLUfu3GrM9d3p` remains READY in the same project. It was retained for rollback; rollback was not executed. The baseline artifact and verification evidence remain archived locally.

[Verified] The exact five audit-created local service processes and disposable PostgreSQL cluster were stopped. Their six ports are closed. Existing user services, simulators and partner-project source were not modified. Only disposable local investigation records were used and cleaned up. No production migration, destructive data operation, new paid service or account-security change occurred.

## Evidence and remaining gaps

[Verified] [Release summary](release.json), [complete public/configuration readback](production-readback.json), [production matrix](production-matrix.json) and [post-release cache visits](warm-cache-after.json) contain the detailed observations. The earlier [audit](README.md) and [local verification](verification.json) remain unchanged as predeployment records. This evidence-only follow-up does not rebuild or redeploy the application artifact.

[Unknown] Physical-device acceptance, full VoiceOver, native Safari, independent financial semantic certification and a new full held-out model qualification remain unestablished. Automated WebKit and bounded source/policy checks are reported as such. The historical catalog and single-owner local execution limits remain intentional.
