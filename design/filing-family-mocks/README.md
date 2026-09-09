# Filing family: five typography studies

**Approved Digest direction: 원형, including the ExtraBold Korean titles.**
The owner approved applying and saving the refined design on 2026-09-09.
The selected page is `digest.html?v=1&lang=ko`; the English counterpart is
`digest.html?v=1&lang=en`. Headline periods are removed, the Korean hero uses
the English maximum display scale, and both lines of every scope-band cell
are centered. Other directions remain comparison evidence.

The original five studies remain local comparison evidence. The selected Digest
direction was subsequently published in Filing Digest PR #21. Agent screens and
icon studies remain proposals; Agent production files have not been changed.

## Consolidated Agent proposal

The owner approved this rendered direction on September 9. These files preserve
the approved prototype; integration into the application is a separate change.

Open http://localhost:4178/agent-final.html?lang=ko&v=1 for the proposed entry
screen and three authentic replay scenarios. The header links to the paired F
icon proposal at `icons-final.html`. Both pages offer Korean/English and light/dark.

Shared paper, Pretendard, and ExtraBold Nanum Myeongjo connect the services.
Agent uses serif type only for its entry invitation, with sans-serif investigation
headings, ruled reported figures, a smaller calculated change, and blue evidence
selection. Desktop selection updates the adjacent source; mobile opens a full-height
dialog with close/Escape and focus return. The F proposal adds one small open
corner while preserving the original Digest icon. It remains a CSS composition
for owner review, not an installed icon asset.

The entry preview uses recorded examples and explicitly does not submit or save
questions. First-use guidance is available beside the verified coverage table.
Only the static preview server on 4178 is needed; the obsolete Digest preview,
Agent runtime, and Agent-specific PostgreSQL instance were stopped on September 9.

## Open

From the Filing Agent repository:

```sh
python3 -m http.server 4178 --bind 127.0.0.1 --directory design/filing-family-mocks
```

Open http://localhost:4178/?v=1&lang=ko. Use the bottom picker, number keys 1–5,
or left/right arrows. The top tabs switch between Digest, Agent, and icons.
“전체 화면” opens the selected page without review controls. The language toggle
is inside the product header and remains available while scrolling. A direct
`lang` parameter overrides the stored preference; without one, the stored
choice takes priority over the browser language. Theme choice is also local.

| Direction | Main decision | Tradeoff |
| --- | --- | --- |
| 1 원형 | Bold Nanum Myeongjo headings with the original Digest hierarchy | Familiar editorial character; more space devoted to headings |
| 2 서문 | Regular Nanum Myeongjo, smaller headings, 2.0 body leading | Sustained reading; quieter first impression |
| 3 명료 | Pretendard headings and short sentences | Fast comprehension; less of the original serif character |
| 4 대조 | Large, brief serif headings and restrained supporting text | Strong hierarchy; requires deliberate line editing |
| 5 실무 | Smaller Pretendard headings and denser spacing | More scope visible at once; less spacious rhythm |

All five preserve Digest's original section sequence: hero, scope band,
recorded walkthroughs, eight actual screens, evidence model, source links.
English body copy and display typography remain the reference, not five
independent English redesigns. Korean headings have deliberate phrase breaks;
words can still wrap on narrow screens.

Agent retains the common paper/ink palette and F while using ink blue, aligned
figures, question history, and a separate evidence panel. Its study includes
three actual recordings and a representative local entry screen. The entry
screen links to the real local application; it does not pretend to run a model.
Icon studies compare the preserved Digest app icon with five small Agent mark
details. They are CSS compositions for selection, not installation-ready icons.

## Assets and factual boundaries

- Digest HTML, baseline CSS, screenshots, GIFs, and marks: read-only copy from
  `../filing-digest/docs/`, at `adfa6bc`.
- Digest installed app icon: existing iOS asset catalog, copied unchanged.
- Agent answers, facts, source identifiers, original units, and timing:
  `slice/replay/recording.json`, at `6f09b5d`, copied without new inference.
- Korean captures already existed. Original company names and source-language
  evidence remain unchanged. This work does not relabel footage as freshly
  recorded or as the expanded 18-company corpus.
- Pretendard: existing Agent font with its OFL license.
- Nanum Myeongjo regular/bold: Google Fonts `ofl/nanummyeongjo`, with OFL license.
  Fonts are bundled locally so runtime rendering makes no font CDN request.

Design dials: ENERGY 1 / RHYTHM 2 / MOTION 1. The phone shadows belong to the
preserved device presentation; ruled sections organize the source narrative.
Agent's blue identifies investigation/evidence actions. Shared brackets identify
filing sources; the service name remains the primary small-size identifier.

The prototype picker follows the installed picker design. Its width is intrinsic
and its labels do not wrap, correcting the narrow-screen shrink-to-fit failure
observed with the unmodified picker CSS. Labels omit redundant visible numbers;
accessible names and keyboard shortcuts retain 1–5.

## Verification, 2026-09-09

PASS — All five Korean Digest directions visually inspected in Chrome at desktop
size; each keeps the full original section order and authentic screenshots.

PASS — All 15 combinations (five directions × Digest/Agent/icons) loaded at
320px viewport width in Korean light and English dark; document scroll width
matched its client width (305px after the browser scrollbar). All 15 English
light combinations also passed this overflow check. Korean Digest was checked
separately at 390px. No missing images in the Korean narrow-width sweep.

PASS — Rendered text contrast check found no below-threshold text in all 15
English light combinations and the three Korean dark surfaces for direction 1.
Thresholds: 4.5:1 normal text, 3:1 large text. This is a targeted DOM-color check,
not an independent accessibility certification or exhaustive screen-reader audit.

PASS — Both Digest recordings play and stop; language updates all page copy and
playback labels. Native browser interaction keeps the evidence section visible
when switching languages (179px below the viewport top with a 163px header).
The section is preserved, rather than a pixel-identical sentence position.

PASS — Agent comparison, company switch, withheld-evidence state, local entry,
source dialog, and previous/next question controls were exercised. NAVER's original
unit is `원`; Samsung's is `백만원`. Escape closes the source dialog and returns
focus to its figure. Values and timings come from the recording.

PASS — Shared mark views, language/theme controls, and variant selection were
exercised. JavaScript syntax checks pass. The checked Chrome session reports no
console errors or warnings.

Final review should choose a direction and any cross-direction elements before
integration. Publication and installed app-icon replacement remain separate steps.

## Selected direction refinement · 2026-09-09

The owner chose 원형 for refinement. Korean and English page headings omit
periods; body sentences retain their punctuation. This is the owner's standing
headline preference. The Korean hero now shares the English maximum display
size (126.4px), with a narrower-screen limit to preserve its two phrase lines.
Both lines in every scope-band cell are centered in both languages.

PASS — Browser inspection found no periods in 원형 h1/h2/h3 in either language;
both desktop hero sizes measured 126.4px. All four band cells use centered text
and centered cross-axis alignment. At a 320px viewport, Korean document and
scroll width both measured 305px; the headline remained two lines. No live
site has been published by this refinement.

The owner then requested a Korean heading weight closer to the English serif.
The selected Digest direction now uses the actual Nanum Myeongjo ExtraBold font
(800) for hero and section headings, without synthetic bolding. Body weight and
spacing are unchanged. The added font is covered by the bundled Nanum OFL.
PASS — Chrome reports heading weight 800 and body weight 400. Desktop visual
inspection and 320px overflow checks passed; no heading periods were introduced.
