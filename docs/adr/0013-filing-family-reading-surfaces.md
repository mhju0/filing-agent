# Add reading surfaces and Filing family typography

Date: 2026-10-01.

## Decision

The public replay opens on an Overview, followed by Recorded runs, a Ledger of every verified figure, and a 공시 Guide. The local application shows Investigate, Ledger and Guide. The Ledger reads `ledger.json`, which `slice/scripts/ledger.py` copies from the pinned snapshot without calculation.

The Ledger derives operating margin, net margin and year-over-year change in the browser through `slice/web/src/format.ts`. Ratios use BigInt arithmetic and round half away from zero to match `Decimal` `ROUND_HALF_UP` in the financial policy. `format.test.ts` pins the recorded Samsung revenue comparison. This is a display-only exception to ADR 0008: investigation answers still come only from the shared financial policy, and no Ledger value is stored or fed back into an answer.

Typography follows the Filing family. A Hangul and ASCII subset of Nanum Myeongjo Bold, renamed Filing Serif KR as the OFL Reserved Font Name requires for a modified font, sets Korean display headings. English headings use the system serif. Pretendard remains the body face. Corners are 2px. `word-break: keep-all` applies to the whole document because English pages contain Korean names, excerpts and 조/억 values; it does not change Latin line breaking.

Korean copy uses 합니다체 and writes fiscal years as `2023 회계연도`. Korean money uses `258.9조 원`, and Korean dollar amounts use whole 억 (`2,451억 달러`). Negative values use U+2212.

## Reasons

- First-time readers need to know what 공시 is and what the app can answer before a recording starts.
- Margins and growth answer common filing questions from figures already verified, without new extraction.
- Keeping derived ratios out of the Python policy avoids changing verified answer behavior for a static page.
- A shared serif, palette and corner treatment connects Filing Agent to Filing Digest, while the brown accent keeps the two products distinct.

## Consequences

Any change to ratio rounding in the financial policy must update `format.ts` and its tests. Moving Ledger ratios into the policy and emitting them in `ledger.json` remains an open alternative. The replay release allowlist must add the font, `ledger.json` and the font notice before the new replay is deployed.
