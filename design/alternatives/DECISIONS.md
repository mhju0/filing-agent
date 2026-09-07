# Filing Agent — decisions record and next task

Paste into Codex. Sections 1–4 are decisions; section 5 is the task.

## 1. Locked product decisions

| # | Area | Decision |
|---|---|---|
| 1 | Navigation | Compact top bar: New investigation, History, scenario tabs (replay only), overflow menu. History = slide-over drawer, closes on selection. No persistent sidebar. Coverage on start screen. Single user, no accounts. |
| 2 | Layout | Desktop: conversation full-width; evidence panel opens to ~45% on figure click; independent scroll; selected figure stays highlighted. **No hover preview.** Figure chips carry inline period: `258.9조원 ·2023`. Mobile: two-detent bottom sheet (peek ~40% / full). Replay: panel pre-opened on turn 1 to the first figure's source. |
| 3 | Answers | Answer card: hero figure(s) → one-line answer → aligned rows or table (2+ periods/companies) → collapsible explanation → muted limitations footer. No default charts. Reported figures: filing chip. Calculated figures: `계산됨 / calc` badge, no filing chip; badge opens "show your work" (formula + operand chips). Both hero variants rendered in alternatives. |
| 4 | Source panel | Excerpt (figure highlighted) → metadata strip (company · filing · period · 연결/별도 · units) → reconciliation: full line only when scale/rounding changed, otherwise `원문 그대로` → external DART/EDGAR link, deep-linked and labelled `(해당 페이지)` only when validated → limitations if any. No PDF viewer. |
| 5 | Prompt & context | Bottom prompt. Context chips show **confirmed** context only; after submit, a changed chip is briefly highlighted `2023 → 2022`. Coverage matrix (≤ ~8 companies × ~6 years; becomes picker + range beyond). Examples fill, don't send. |
| 6 | Recovery | Ambiguity: 2–3 tappable choices in the assistant turn. Missing/partial: same card shape, `—` + reason; evidence panel shows search trail, always. Failures: inline card, plain cause, one visible retry, prompt preserved, validated partials kept. |
| 7 | Progress | Real pipeline step list with ✓/running/pending and elapsed seconds; running step names its target. Finished list = search trail. Cancel available immediately; UI shows `취소 요청됨 · 정리 중` until runtime confirms. Replay shows completed list + `recorded · Ns actual`. **Timing targets parked until benchmark.** |
| Q1 | Scope | v1 explains numerical relationships only. "Why" questions get a scope refusal that points to the filing section (`사업의 내용` / MD&A ↗). |
| Q41/42 | Saved | Saved = frozen, read-only. "이어서 질문하기" forks a new investigation with lineage chip `← 저장본 <date>에서 이어짐`. Reruns use the same chip. |
| Q44 | Replay entry | Land directly in the annual comparison; three tabs in the top bar, third labelled `증거 부족 사례 / Insufficient evidence`; persistent `녹화된 시연 · Recorded demo` label. |
| Q52 | Language | One UI language at a time. Bilingual only for source excerpts (original + labelled translation on demand) and glossary terms `Revenue (매출액)`. Language switch is a visible replay action. |
| Q74 | Stack | FastAPI + **LangGraph (checkpointer used for cancel/resume; not decorative)** + PostgreSQL + React/Vite. Local inference via Ollama first; MLX compared only if measurements justify. `OLLAMA_NO_CLOUD=1`. |

## 2. Remaining Owner questions — resolved by default

| Q | Default |
|---|---|
| 8 | Deferred until benchmark. Order of reductions if quality is insufficient: (1) narrower metric set, (2) reviewed answer templates, (3) fewer companies/periods, (4) another local model. Never cloud. |
| 11 | History is an overlay; active run continues. Starting a new investigation during a run asks once before cancelling (one model at a time on this hardware). |
| 13 | Language, theme, runtime status live in a right-side overflow menu; runtime status is a small dot (green/amber/red) with tooltip, not text. |
| 34 | "One retry" = one visible user action. One silent transport retry for connection errors only. Runs carry an idempotency id; a retry reuses it. |
| 37 | Cancel immediate (see 7). |
| 40 | Auto title `회사 · 지표 · 기간` from the first resolved turn; renameable; text search; sort by last activity. Save = explicit button, not auto. |
| 43 | Expiry shown per item in History (`14일 후 만료`); delete via item menu with undo toast; export/import (JSON + evidence snapshot) in overflow menu. Activity = opening or adding a turn. |
| 66 | Own identity, companion relationship: share Filing Digest's type family and neutral palette; distinct accent and wordmark. *(Owner may override — taste.)* |
| 68 | Three alternatives, see section 5. |

## 3. Engineering defaults (document; don't ask)

- **Q2 responsibility split:** model does question→structured intent JSON, answer/explanation/refusal prose, UI translation. Code does company/metric alias resolution, retrieval, arithmetic, unit/basis/period compatibility, refusal *decision*, validation. The model never emits a number that code didn't supply.
- **Q5:** prefer latest restatement; withhold comparisons across 연결/별도, mismatched fiscal years, or currencies; percentage change withheld for nonpositive baseline (absolute diff still shown).
- **Q12/46:** URL carries investigation id, turn index, selected source id (and scenario id in replay). Draft persists in localStorage-equivalent app state; scroll position best-effort.
- **Q15:** on panel open, keep the selected figure's viewport offset (measure before/after, scrollBy delta).
- **Q20:** limitations that change interpretation (basis, restatement, partial period) render as a small inline tag next to the figure; everything else in the footer.
- **Q27:** explicit text wins over chips; if both changed and conflict, clarify (decision 6 shape 1).
- **Q30:** Enter sends, Shift+Enter newline; ignore Enter during IME composition (`isComposing`); draft persists per investigation.
- **Q33:** a partial figure survives only if it passed validation (source present, unit resolved, basis known).
- **Q38:** LangGraph checkpoint per step; on restart, resumable runs show a "재개 가능" card; otherwise the interrupted card from decision 6.
- **Q49:** KR/EN recordings are separate assets keyed by scenario + turn index; if a turn is missing in one language, show the other with a translation label rather than fail; asset load failure shows an inline error card, never a blank.
- **Q50:** Pretendard (Korean + Latin, tabular figures via `font-variant-numeric: tabular-nums`); fallback Noto Sans KR. Test with real fixture content, not lorem.
- **Q51:** Korean displays 조/억 with source units in reconciliation; English displays trillion/billion KRW with the same reconciliation; negatives with `−` (U+2212), never parentheses; `—` for withheld; `≈` only when rounding was applied.
- **Q53:** one glossary file (`glossary.json`) is the single source for filing names, metrics, basis, refusal strings, calc labels, in both languages.
- **Q57:** theme preference persisted; inline script sets `data-theme` before first paint to avoid flash.
- **Q60/61:** drawers/sheets/popovers trap focus, close on Escape, return focus to the opener; progress and new results announced via a single `aria-live="polite"` region; errors via `assertive`.
- **Q65:** reduced motion → instant state changes with a 1-frame opacity fade; no layout-shifting transitions ever.
- **Q71–73, 77:** local API binds 127.0.0.1 only; validates `Origin`/`Host`; CSRF token on mutating calls. Model output and excerpts rendered as text, links allow-listed to DART/EDGAR domains. Logs: no question text by default; diagnostics opt-in; replay export contains only scenario assets. Replay build has zero network calls (CI check greps for fetch/XMLHttpRequest to non-asset URLs).
- **Q75:** ids: investigation, run, turn, fact, calculation, source, snapshot, replay_event — all ULIDs; facts and sources reference a Filing Digest snapshot id.

## 4. Still open, by design

- Benchmark unrun (Ollama not installed). Q6, Q7, Q8, Q33 thresholds, Q37 timing, timing targets in decision 7 all wait on it.
- Q3 coverage: needs a read-only inventory of Filing Digest (companies × years × metrics with verified sources).
- Two taste questions for the owner after alternatives render: Q18 (hero variant) and Q66 (identity).

## 5. Task — render three design alternatives of the investigation screen

Use UI UX Pro Max and Emil's design-engineering skill for implementation quality; Antislop applies. The decisions above are the direction; skills do not replace it.

Build three **static React + Tailwind** pages (no backend, no model) under `design/alternatives/`, each rendering the *same* investigation from `bench/fixtures/samsung_is.json`: the annual-comparison case (Samsung 매출액 2023 vs 2022), with the evidence panel open on the 2023 figure. Korean UI, light theme; include a dark-theme toggle and an English toggle if cheap, otherwise stub them.

The three must differ in **hierarchy and composition**, not accent colour:

- **A — Reading first.** Prose-leaning answer card; hero = calculated change (−14.3%, `계산됨`); figures in aligned rows beneath; evidence panel as a quiet side column.
- **B — Ledger.** Table-leaning; hero = the two reported figures side by side with the change in a third, visually subordinate column; dense numeric typography; evidence panel with the excerpt rendered as a mini table fragment.
- **C — Card stack.** Each element (hero, rows, explanation, limitations, search trail) is a distinct card with clear edges; evidence panel is a stacked sheet-like column that previews the mobile bottom-sheet behaviour on desktop.

Each alternative must show: context chips above the prompt (confirmed state, with `2023` highlighted as the changed chip), a completed step list acting as the search trail, the reconciliation line (`258,935,494 백만원 → 258.9조원`), a `계산됨` badge that expands to show the formula with two operand chips, the `Revenue (매출액)` glossary treatment, and the external link labelled per decision 4.

Also produce, per alternative, a narrow (390px) screenshot with the bottom sheet at peek detent.

Deliver: `design/alternatives/README.md` with side-by-side screenshots (desktop + mobile) and a 5-line comparison on readability, hierarchy, source discoverability, and Korean/English fit. Do not recommend one; I'll choose. Do not touch `bench/`, `docs/`, or Filing Digest.

Commit:
```
git add design
git commit -m "Add three static design alternatives for the investigation screen"
```
