# Local model benchmark

Recorded: 2026-09-07T09:33:56.113515+00:00

Status: complete.

| Model | Case | Median seconds | Accuracy | Parse rate | Hallucinations | Notes |
| --- | --- | ---: | --- | --- | ---: | --- |
| qwen3:8b | compare | 57.51 | 0/3 | 3/3 | 12 | Invented numbers: `14.38`, `14.38`, `100`, `-14.38`, `14.38`, `14.38`, `100`, `-14.38`, `14.38`, `14.38`, `100`, `-14.38`; Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |
| qwen3:8b | switch | 79.83 | 0/3 | 3/3 | 3 | Invented numbers: `967,064`, `967,064`, `967,064`; Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |
| qwen3:8b | missing | 21.30 | 3/3 | 3/3 | 0 | Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |
| gemma4:e4b | compare | 51.10 | 0/3 | 0/3 | 12 | Invented numbers: `-14.45`, `14.45`, `100`, `-14.45`, `-14.45`, `14.45`, `100`, `-14.45`, `-14.45`, `14.45`, `100`, `-14.45`; Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |
| gemma4:e4b | switch | 67.64 | 0/3 | 0/3 | 0 | Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |
| gemma4:e4b | missing | 17.29 | 3/3 | 3/3 | 0 | Refusal gate: passed 3/3 missing trials; inspect bilingual prose manually |

Three trials per case. Switch accuracy and parsing require both turns to pass; its time is the two-turn total.
Median includes attempted failures/timeouts, excludes unattempted runs. Each case has a 120s wall deadline.
Hallucinations count unsupported numeric occurrences (including prose), not unique numbers. Correct, validated calculations are exempt.
Refusal violations also include returning an unrelated supplied figure. See results.json for raw visible answers, sources, per-turn metrics and gate reasons.
Times include model loading: keep_alive=0 unloads after every turn. No warmup, no parallel generation. Runtime may retain OS file cache.
No model is selected automatically. This is a structured-table diagnostic, not a DART extraction or bilingual semantic-quality certification.
