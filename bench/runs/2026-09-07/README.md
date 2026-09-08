# Local feasibility evidence — September 7, 2026

**Gemma 4 E4B is the provisional candidate for an intent-only vertical slice. Qwen3 8B is disqualified.** Local execution is feasible for the bounded verified catalog when code owns evidence selection, refusal policy, arithmetic and financial wording. Neither model passed the original full-answer contract. No production latency promise, complete application, or public replay is established.

All **117 case runs / 141 chat responses** completed locally. Raw failures are preserved. [Offline artifact verification](verification.json) rechecks input hashes, scores, figures and source bindings; [semantic review](semantic-review.json) records findings that numeric checks miss.

## Results and what they mean

| Experiment | Qwen3 8B | Gemma 4 E4B | Meaning |
| --- | --- | --- | --- |
| Original table → full answer/source JSON | 3/9 case checks | 3/9 case checks | Both passed only the basic missing-evidence case. Arithmetic, formatting or duplicate JSON keys failed the other cases. |
| Verified catalog → intent, evidence IDs and generated sentences | 18/33 mechanical checks | 27/33 mechanical checks | These scores exclude prose semantics. Both falsely said Samsung revenue increased. Qwen also invented missing R&D as zero and substituted Samsung for NAVER in a missing-year follow-up. |
| Question → intent JSON → code-selected evidence and answer | Excluded after fabrication | **33/33 case checks; 39/39 turns parsed** | Code produces the correct figures, calculation, refusal state and bilingual financial sentences. This is the viable architecture experiment. |

The three experiments do different work and use different output contracts. Their timings are not a controlled comparison of model speed alone. The final experiment also uses JSON Schema output and a 4,096-token context instead of JSON mode and 8,192 tokens. No failed score was overwritten or retroactively counted as a success.

- [Original report](original/results.md) / [raw responses](original/results.json): three runs each for comparison, company switch and missing evidence, unloaded after every turn. The older issuer-publication fixtures remain unchanged.
- [Verified-pilot report](pilot/results.md) / [raw responses](pilot/results.json): eleven cases per model, three runs each, using the same complete 15-fact regulator-bound catalog. Its `accuracy` field means mechanical intent/evidence agreement, not complete answer correctness.
- [Intent-only report](intent/results.md) / [raw intents and code-produced answers](intent/results.json): the same eleven cases, with the model interpreting company, metric, fiscal years, basis and requested action. It receives no financial values. Code resolves the verified catalog and full source bindings without receiving the test oracle.

## Failures that change the implementation

**Refusal quality disqualifies Qwen3 8B.** All three adversarial R&D trials stated that the absent expense was reported as `0`, in Korean and English. The basic refusal smoke pass did not survive pressure to invent a figure. In the NAVER follow-up, all three trials silently selected Samsung's FY2022 revenue when NAVER's requested year was unavailable. A valid source ID alone does not establish a valid answer.

**Generated prose needs more than numeric scanning.** Both models selected the correct Samsung revenue IDs while claiming revenue increased; the verified change is **−14.33%**. Neither generated sentence contained an invented financial numeral, so mechanical checks passed. The final experiment derives direction and both language versions from the same Decimal calculation. This does not prove that a separate, grounded prose-generation pass could never work; it establishes that the tested single-pass sentences are unsuitable for display.

**Gemma's safe text did not guarantee coherent state.** Under the zero-pressure request it withheld the amount in prose but returned `operation: report` and `refused: false`. In the missing-year follow-up it correctly kept NAVER and refused, but still used `operation: report`. It did not fabricate a missing amount in these trials. Code therefore owns whether an answer is a report, a refusal or a clarification; model-generated policy flags are not authoritative.

**Keep source objects and number formatting out of generation.** Qwen's original comparison consistently returned −14.38%; Gemma returned −14.45%. Gemma also duplicated source keys, which strict parsing rejects. Qwen's Korean NAVER amount was `967,0643.576585백만원` despite a correct structured value and English amount. The scanner flags the fragment `967,064`; that is a malformed grouping defect, not proof of an invented underlying amount. It also flags formula constant `100` when a calculation fails; that token is not itself a fabricated financial fact. The raw numeric counts require this interpretation.

Safe refusals with a wrong metric/reason field remain contract failures, distinct from fabrication. Both models' currency-refusal sentences were too broad: the requested percentage must be withheld, while side-by-side figures remain possible. The final experiment uses specific curated refusal copy.

## Measured latency and memory

On this Mac, the final Gemma experiment's warm single-turn cases took **1.47–1.81 seconds**; their median was **1.64 seconds**. Warm two-turn case totals were about **5.65–5.74 seconds**. The first run after a model unload took **6.37–10.55 seconds**, with the upper value representing both turns of a conversation. These timings include local chat and code resolution, not a complete web application or fresh filing acquisition.

| Experiment/model | Peak sampled Ollama process RSS | Highest sampled system swap | Observed pressure codes |
| --- | ---: | ---: | --- |
| Original / Qwen | 5.66 GiB | 7,119 MiB | 1, 2, 4 |
| Original / Gemma | 4.40 GiB | 7,124 MiB | 1, 2 |
| Verified pilot / Qwen | 5.67 GiB | 7,060 MiB | 1, 2 |
| Verified pilot / Gemma | 4.61 GiB | 7,020 MiB | 1, 2 |
| Intent-only / Gemma | 4.38 GiB | 6,980 MiB | 1, 2 |

The final profile's largest Ollama-reported model allocation was about 3.20 GB. Process RSS can double-count shared pages and omit GPU allocations; neither number is whole-app peak RAM. Pressure codes are the dispatch flags exposed by the sysctl: 1 normal, 2 warning, 4 critical. The mapping was checked against the local macOS SDK's `dispatch/source.h` and Apple's [sysctl implementation](https://github.com/apple-oss-distributions/xnu/blob/main/bsd/kern/kern_memorystatus_notify.c). It must not be confused with the kernel's separate internal pressure enum.

The machine already used about 4.2 GiB of swap before installation. It had about 6,980 MiB at the beginning of the final profile, after earlier experiments. Swap is system-wide and persists after unloading; it cannot all be attributed to the current model. Existing applications stayed open. Cold means model-unloaded, not cleared OS file cache. Trials were serial and ordered, not randomized. The full application's memory headroom remains a required measurement.

## Environment and local-only boundary

Apple M1 Pro, 16 GiB unified RAM, macOS 26.6.2; Ollama **0.33.3**. No account or sign-in was used. Exact downloaded tags were `qwen3:8b` (about 5.2 GB) and `gemma4:e4b` (about 9.6 GB). No EXAONE model was already installed, so none was added to the requested baseline. Download size is not inference memory: the larger Gemma download used less measured memory in these text-only runs. [Qwen tag](https://ollama.com/library/qwen3:8b), [Gemma tag](https://ollama.com/library/gemma4:e4b).

The controlled server used `127.0.0.1:11434`, one loaded model, one parallel generation, flash attention and `q8_0` KV cache. `OLLAMA_NO_CLOUD=1` was set on the server, which logged `Ollama cloud disabled: true`; persistent `~/.ollama/server.json` also sets `disable_ollama_cloud: true`. The listener was checked with `lsof`; model tags, positive local weights, digests and architecture metadata were checked before generation. Model downloads used the network; all inference used loopback and local weights. No cloud model calls, tunnel, login service or public deployment were used. These are runtime/configuration checks, not a packet-capture certification. [Ollama local-only configuration](https://docs.ollama.com/faq).

Gemma digest: `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`. Final configuration: temperature 0, seed 42, context 4096, output cap 256, thinking disabled, five-minute keep-alive within each case, explicit unload between cases. The final response format is a JSON Schema, independently checked by the client. Schema enforcement does not establish semantic correctness. [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs).

Homebrew installed Ollama 0.33.3, MLX 0.32.1 and MLX-C 0.6.0_4, and upgraded required OpenSSL 3.6.4, SQLite 3.53.4 and Python 3.14.7 dependencies. The benchmark itself uses a project-local Python 3.11 virtual environment with `requests`; exact packages and setup checks are in [setup.json](setup.json). No source or environment in Filing Digest was modified; its pinned revision and pre-existing untracked file were unchanged on the final check.

## Limits and next gate

This establishes a **provisional intent-parser candidate for the bounded vertical slice**, not a generally reliable financial assistant. The known eleven cases are repeated with fixed temperature/seed, not held-out independent samples. The vocabulary explicitly contains the three supported metrics plus R&D. Unknown metric wording, varied company aliases, relative fiscal years, negation, clarification continuation, and longer conversations still need a separate evaluation. The benchmark does not implement a durable pending-clarification state; its clarification case checks only the initial response.

The test oracle is used only for scoring, never to choose a runtime answer or correct model history. Even schema-valid intent can be wrong. Production must validate explicit company changes against accepted context, preserve pending clarification separately, and reject ambiguous or unsupported interpretation rather than retrieving a convenient substitute. Full source taxonomy is retained: the pilot admits both the known DART `consolidated` and EDGAR `consolidated_entity_total` bases for consolidated requests; it does not declare all cross-regulator net-income definitions equivalent.

Next, use the pinned Gemma configuration in one bounded question → intent → verified evidence → code calculation/answer → save → static replay slice. Verify context changes, clarification recovery, cancellation, interruption/retry, persistence, replay without the Mac, and actual UI/backend memory together. Financial prose must come from validated claims; an optional model explanation needs its own evidence checks and evaluation. Do not reuse failed raw outputs as successful replay answers.

Public DART navigation remains unresolved; verified local source content does not establish a working external viewer. No PDF/HTML reading by a small model, full-corpus extraction, broad translation quality, fresh-data retrieval, complete application or authentic public replay was demonstrated here.

## Reproduce and verify

From the repository root, start `./bench/serve.sh` in a separate terminal. Use fresh output directories when changing a prompt, runtime or model:

```sh
BENCH_OUTPUT_DIR=bench/runs/new-original .venv/bin/python bench/run.py
PILOT_OUTPUT_DIR=bench/runs/new-pilot .venv/bin/python bench/pilot.py
INTENT_OUTPUT_DIR=bench/runs/new-intent .venv/bin/python bench/intent.py
```

The first two suites compare both installed candidates; the third defaults to Gemma, since Qwen was disqualified. To recheck these recorded results without inference:

```sh
.venv/bin/python bench/verify_results.py
.venv/bin/python -m unittest discover -s bench/tests -v
```

The evidence-source audit also passed offline again. Harness verification passed 31 tests, including a real worker deadline, wrong-company/period/source rejection, source-snapshot corruption, refusal behavior, nonpositive/comparability checks and bilingual direction when a nonzero change rounds to 0.00%. No timeout occurred in the actual model trials, so runtime cancellation remains unproven. The controlled server was stopped after all models were confirmed unloaded. The runtime and downloaded weights remain installed; no startup service was configured. Start the server with `./bench/serve.sh` when needed.
