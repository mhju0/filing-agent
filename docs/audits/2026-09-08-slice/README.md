# Local application and public replay release audit

September 8, 2026. The owner authorized completion, section-by-section verification and public deployment. The live app remains on the Mac; only an explicit static export is eligible for hosting. Deployed to https://filing-agent.vercel.app. Anonymous artifact hashes and endpoint boundaries are recorded in `deployment.json`. Vercel initially auto-connected the parent private GitHub repository; that connection was explicitly removed. Future releases must deploy the reviewed static directory through the CLI.

## Implemented scope

`slice/` contains a React/TypeScript Ledger interface, FastAPI loopback API, three-stage LangGraph with native PostgreSQL checkpoints, separate Agent PostgreSQL storage and pinned Ollama/Gemma intent interpretation. Evidence, arithmetic and bilingual financial wording are code-owned. The model does not read filings. Fifteen audited historical facts cover three companies and three reported metrics; missing R&D evidence is a collection limitation, not a claim about the full filing.

The app supports company/year/metric clarification, source and formula inspection, partial supported results, confirmed cancellation, one explicit retry, saved immutable investigations, continuation and refresh into new IDs, history search, deletion, private backup/restore, expiring diagnostics and thirty-idle-day ordinary retention. Expiry is checked on direct access and periodic cleanup; deleting the active investigation removes its browser draft. Source snapshots and preserved answers are never silently replaced.

## Verification evidence

| Boundary | Observed result | Evidence |
|---|---|---|
| Source collection | All fifteen values/source identities round-trip; DART original amounts verified; SEC automated browser denied | `source-navigation.json`, September 7 coverage audit |
| Local model baseline | Gemma intent-only selected after Qwen fabrication and generated-prose failures | `../../../bench/runs/2026-09-07/README.md` |
| Wider application evaluation | Development 80/80 after retained failures; execution-held-out 120/120 across three trials, 138 turns | `../../../evals/RESULTS.md`, `../../../evals/results/` |
| Refusal/context | Each language/trial 10/10 supported and 10/10 withheld/clarification; no source/value mismatch | `../../../evals/release-summary.json` |
| Network boundary | Application and model outbound denied except localhost; negative external and positive local controls | `offline-verification.json` |
| Memory | Existing user-app workload; normal and warning pressure; peak model RSS about 3.97 GiB, aggregate owned process RSS about 5.11 GiB, system swap peaked about 6.53 GiB | `combined-memory.json` |
| Process interruption | SIGKILL during actual interpretation; startup marked interrupted; explicit retry after confirmed model unload produced exact answer | `restart-check.json` |
| Real capture | Three saved investigations; comparison -14.33%, explicit company switch, missing R&D refused; clarification and cancellation also checked | `capture.json` |
| Actual browser video | Unedited fresh question and company follow-up, with real execution pauses | `actual-run.webm`, `actual-run.json` |
| Unit/integration checks | 12 application tests and 31 benchmark tests passed; source ZIP extraction also passed both suites | `slice/tests`, `bench/tests` |
| UI | Bilingual/theme screenshots, 320/390px reflow, keyboard containment/return, formulas, save/continue/refresh/clarification/edit; no axe A/AA violations in checked states | `live-browser.json`, `replay-browser.json` |
| Public materials | KO/EN notes at 1440/390/320px; links and axe checks; missing recording recovery | `release-browser.json` |
| Static isolation | App and Ollama stopped; replay navigation used no API or off-origin requests | `replay-browser.json` request list |
| Build | Strict TypeScript/Vite build, Ruff and `git diff --check` pass; extracted archive build also passes | Package locks and source archive manifest |

Timings in the 138-turn held-out set: median 2.96s, observed p95 3.19s, maximum 9.78s. Mostly warm, first turn includes loading. Cases are agent-authored paraphrases of the same known task families as development. This is neither independent accounting review nor arbitrary financial-language certification. The score applies to the guarded application, not the model alone. Subsequent changes address storage expiry, browser drafts, backup preservation, UI and formatting; no final model-policy retuning followed the held-out set.

## Retained problems and limits

- `initial-clarification-failure.json`: company-free question led to a model guess before explicit-context guards.
- Development records retain the missing SEC `section` adapter error and safely blocked English company follow-up. These are not removed from the experiment record.
- Browser checks exposed modal Tab escape, a fast-new-investigation draft race and a draft deletion gap. These were fixed and checked again.
- Backup restore initially demanded exact equality with today's partial-answer policy, rejecting a valid historical answer. Restore now checks source-bound figures and arithmetic while preserving historical wording; checksums detect accidental alteration, not a malicious backup author.
- SEC automated browser denial remains disclosed; DART filing-level navigation does not promise exact table-cell navigation or permanent availability.
- Only M1 Pro 16 GiB was measured. Memory pressure was not always normal. No 8 GiB or clean-machine memory guarantee is made.
- This is a single-owner loopback application. PostgreSQL trust authentication does not protect against other local processes. Production cloud operations and live hosted questions are outside the release.
- The native theme bootstrap emits Vite's informational classic-script warning. It is intentionally served from `public/theme.js` before first paint, and its built asset/request is verified. Starlette tests emit an upstream deprecation warning; the checks pass.

## Antislop delivery gate

PASS for the declared, checked release scope. DURING mode; owner-selected Ledger; ENERGY 1 / RHYTHM 2 / MOTION 1.

Design read: a bilingual filing research workspace whose focal point is the paired reported figure and its selected original evidence. Warm paper/ink colors and restrained terracotta connect the answer to its source. Pretendard gives Korean and English a shared reading rhythm; tabular numerals and ruled rows support financial comparison. The separate evidence panel avoids crowding the conversation; full-height mobile evidence prioritizes reading. Transitions are immediate, with no fake processing animation in replay.

- Block 1, hard rules: no fabricated financial facts, testimonials, marketing numbers, ghost links, placeholder figures presented as real, emoji-led marketing or inaccessible hidden preferences. Real capture/source checks support displayed data. Build and interactive browser evidence are retained.
- Block 2, purpose checks: no gradients, glows, glass, background patterns, generic illustrations, decorative icon collection, floating cards or template animations. The sun/moon controls identify theme actions; the external arrow identifies original filing navigation. Badges distinguish calculation/source state. Figure backgrounds show selected evidence. Each technique has a functional reason.
- Block 3, liveliness: all seven checks satisfied by the declared dials, clear figure focal point, deliberate reading space, restrained source accent and repeated ledger rule/number treatment. The selected design direction preceded implementation.
- Block 4, craft: controls act on actual state; the recorded label is persistent; no template-only sections or unsupported product claims. Both themes, bilingual content, narrow widths, keyboard focus, empty/refusal/error/loading states and asset recovery were checked. The public project notes exist to explain implementation, evidence, setup and limitations.
- Measured text contrast: light primary 13.58:1, light secondary 5.26:1, light accent 6.38:1; dark primary 13.46:1, dark secondary 6.71:1, dark accent 7.96:1. Control borders are 3.71:1 light and 4.11:1 dark, meeting the 3:1 non-text criterion; those border colors are not normal text. Raw helper output in `contrast.json` also reports the stricter text threshold for those non-text pairs.

Automated accessibility checks and explicit keyboard/visual inspection support these claims; they are not an exhaustive assistive-technology certification.

## Partner project boundary

Filing Digest remained read-only. End-of-work HEAD: `e1ec00911f3447f4e1317af945e98413a2d961e6`. Its sole observed dirty item remained the pre-existing untracked `docs/CLAUDE_ENV_INVENTORY.md`.

## Deployment procedure corrections

Vercel automatically connected the private repository during initial project creation. The connection was removed and the project's `link` field was subsequently checked. A later source-archive redeploy was accidentally invoked from the repository root and cancelled at the start of its 0.0B upload display. Deployment inventory at that point contained only the original reviewed static deployment; no root deployment was created. The production release was then updated from the reviewed static directory. Root `.vercelignore` excludes all files, and `release/deploy.sh` verifies the exact allowlist/hashes before changing directory and deploying. Public artifact hashes and private-path 404 checks are recorded after the final deployment.

The public browser suite initially read the prior figure count immediately after a scenario change. Repeating the unchanged check reproduced the timing race; waiting for the selected refusal state resolved it. The application assets did not change for that correction. The updated source archive includes the corrected verifier.

Original regulator responses and the upstream font license preserve their bytes in Git through `.gitattributes`; raw source whitespace is not reformatted to satisfy code whitespace checks.
