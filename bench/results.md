# Local model benchmark

Recorded: 2026-09-07T03:33:47.507512+00:00

Status: blocked. Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError

| Model | Case | Median seconds | Accuracy | Parse rate | Hallucinations | Notes |
| --- | --- | ---: | --- | --- | ---: | --- |
| qwen3:8b | compare | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |
| qwen3:8b | switch | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |
| qwen3:8b | missing | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |
| gemma4:e4b | compare | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |
| gemma4:e4b | switch | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |
| gemma4:e4b | missing | N/A | N/A (0/3 run) | N/A (0/3 run) | N/A | Local Ollama preflight failed at http://127.0.0.1:11434: ConnectionError; Refusal gate: not evaluated |

Three trials per case. Switch accuracy and parsing require both turns to pass; its time is the two-turn total.
Median includes attempted failures/timeouts, excludes unattempted runs. Each case has a 120s wall deadline.
Hallucinations count unsupported numeric occurrences (including prose), not unique numbers. Correct, validated calculations are exempt.
Refusal violations also include returning an unrelated supplied figure. See results.json for raw visible answers, sources, per-turn metrics and gate reasons.
Times include model loading: keep_alive=0 unloads after every turn. No warmup, no parallel generation. Runtime may retain OS file cache.
No model is selected automatically. This is a structured-table diagnostic, not a DART extraction or bilingual semantic-quality certification.
