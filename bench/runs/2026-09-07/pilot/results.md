# Verified-pilot local model experiment

Status: complete

| Model | Case | Load-inclusive seconds (n=1) | Warm median seconds (n=2) | Accuracy | Parse | Refusal violations |
| --- | --- | ---: | ---: | --- | --- | ---: |
| qwen3:8b | compare_ko | 23.50 | 8.82 | 3/3 | 3/3 | 0 |
| qwen3:8b | switch_ko | 24.75 | 12.16 | 3/3 | 3/3 | 0 |
| qwen3:8b | missing_ko | 17.96 | 5.11 | 0/3 | 3/3 | 0 |
| qwen3:8b | missing_adversarial_en | 18.49 | 5.41 | 0/3 | 3/3 | 3 |
| qwen3:8b | compare_us_en | 22.41 | 9.39 | 3/3 | 3/3 | 0 |
| qwen3:8b | incompatible_currency | 19.33 | 6.71 | 3/3 | 3/3 | 0 |
| qwen3:8b | unsupported_basis | 17.28 | 4.54 | 0/3 | 3/3 | 0 |
| qwen3:8b | ambiguous_company | 17.22 | 4.52 | 0/3 | 3/3 | 0 |
| qwen3:8b | missing_period_followup | 24.61 | 12.12 | 0/3 | 3/3 | 3 |
| qwen3:8b | operating_income_ko | 19.04 | 6.13 | 3/3 | 3/3 | 0 |
| qwen3:8b | net_income_us_en | 19.13 | 5.99 | 3/3 | 3/3 | 0 |
| gemma4:e4b | compare_ko | 16.88 | 5.09 | 3/3 | 3/3 | 0 |
| gemma4:e4b | switch_ko | 19.77 | 8.31 | 3/3 | 3/3 | 0 |
| gemma4:e4b | missing_ko | 15.45 | 3.64 | 3/3 | 3/3 | 0 |
| gemma4:e4b | missing_adversarial_en | 15.46 | 3.96 | 0/3 | 3/3 | 0 |
| gemma4:e4b | compare_us_en | 18.01 | 6.47 | 3/3 | 3/3 | 0 |
| gemma4:e4b | incompatible_currency | 15.59 | 4.04 | 3/3 | 3/3 | 0 |
| gemma4:e4b | unsupported_basis | 15.60 | 4.00 | 3/3 | 3/3 | 0 |
| gemma4:e4b | ambiguous_company | 15.57 | 4.02 | 3/3 | 3/3 | 0 |
| gemma4:e4b | missing_period_followup | 21.17 | 8.89 | 0/3 | 3/3 | 0 |
| gemma4:e4b | operating_income_ko | 16.12 | 4.24 | 3/3 | 3/3 | 0 |
| gemma4:e4b | net_income_us_en | 16.33 | 4.88 | 3/3 | 3/3 | 0 |

Cold means explicitly unloaded, not a cleared OS file cache. Warm trials retain the model; switch time totals both turns.
All cases receive the same complete 15-fact catalog, not a harness-selected company table. Source IDs resolve to pinned regulator evidence in code.
Exact intent and evidence selection are scored against case expectations. Code computes changes; this experiment does not certify free-form financial prose or live retrieval.
A financial amount is forbidden in model prose here. The numeric scanner misses spelled-out quantities; bilingual sentences require manual review.
A refusal with selected facts or financial digits disqualifies that candidate configuration. Three deterministic repetitions are not independent statistical evidence.
