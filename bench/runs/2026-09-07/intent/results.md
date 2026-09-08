# Intent-only local experiment

Status: complete

| Model | Case | Load-inclusive seconds (n=1) | Warm median seconds (n=2) | End-to-end case checks | Parse |
| --- | --- | ---: | ---: | --- | --- |
| gemma4:e4b | compare_ko | 7.64 | 1.74 | 3/3 | 3/3 |
| gemma4:e4b | switch_ko | 10.55 | 5.74 | 3/3 | 3/3 |
| gemma4:e4b | missing_ko | 6.96 | 1.72 | 3/3 | 3/3 |
| gemma4:e4b | missing_adversarial_en | 6.73 | 1.62 | 3/3 | 3/3 |
| gemma4:e4b | compare_us_en | 6.47 | 1.79 | 3/3 | 3/3 |
| gemma4:e4b | incompatible_currency | 7.00 | 1.60 | 3/3 | 3/3 |
| gemma4:e4b | unsupported_basis | 6.98 | 1.53 | 3/3 | 3/3 |
| gemma4:e4b | ambiguous_company | 6.41 | 1.49 | 3/3 | 3/3 |
| gemma4:e4b | missing_period_followup | 9.26 | 5.65 | 3/3 | 3/3 |
| gemma4:e4b | operating_income_ko | 6.60 | 1.63 | 3/3 | 3/3 |
| gemma4:e4b | net_income_us_en | 6.37 | 1.64 | 3/3 | 3/3 |

Model output is intent only. Code selects source-bound facts, decides refusal, calculates changes, and supplies both financial answer sentences.
Case checks compare the resulting company, metric, periods, selected IDs and refusal state against expectations. Runtime resolution never receives that oracle.
Known closed-vocabulary cases, three deterministic repetitions, no held-out evaluation. This is not a complete app or a certification of arbitrary question understanding.
Cold means model-unloaded, not cleared file cache. Warm switch time is the sum of both turns. See JSON for raw intents, actual context, answers, source bindings, timings and memory.
