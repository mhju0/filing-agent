# Local model benchmark

From the repository root, run all model/case trials and regenerate both reports:

```sh
python3 bench/run.py
```

Python 3.10+ and `requests` are required (`python3 -m pip install -r bench/requirements.txt` if missing). Ollama must already be running on `127.0.0.1:11434` with the desired models installed. This harness never installs or pulls a model and never calls a hosted model. It writes only within `bench/` and does not use the application stack.

Default models are exact installed tags `qwen3:8b`, `gemma4:e4b`, plus installed tags containing `exaone`. Override with, for example, `MODELS='qwen3:8b,exaone3.5:7.8b' python3 bench/run.py`. A tag appearing in the online library does not mean it is installed. `/api/tags` is the API equivalent of `ollama list`; the report retains installed names, digests, sizes, and `/api/show` metadata. Missing tags produce explicit unrun rows. No EXAONE version is guessed when none is installed.

## Local-only boundary

The URL is fixed to IPv4 loopback. Environment proxies and HTTP redirects are disabled. Cloud tags, remote-host metadata, remote model references, and models without verifiable architecture/positive local size are rejected before generation. These checks assume a trusted local Ollama daemon; they cannot constrain a modified daemon's network behavior. Start the **server** with `OLLAMA_NO_CLOUD=1` for Ollama's cloud-disable control. Setting that variable only on this client does not reconfigure an already-running server. Model acquisition is separate from the benchmark runner. [Ollama local-only mode](https://docs.ollama.com/faq)

## What is measured

Three trials each for annual comparison, a two-turn company switch, and missing evidence. Switch passes only if both responses pass; it receives the actual first response in conversation history, including errors. The harness supplies the correct second company's table. This tests contextual answer generation, not autonomous company routing or DART retrieval.

Requests use `/api/chat`, JSON mode, temperature 0, seed 42, an 8,192-token context limit, and a 2,048-token output limit. Thinking is disabled when the model advertises that capability. Runs are serial. `keep_alive=0` releases the model after **every turn**, including between switch turns, to avoid keeping several models in limited RAM. There is no warmup: wall time includes load and process/HTTP overhead, with possible OS file-cache effects. These are conservative load-inclusive measurements, not warm interactive latency. Reported `eval_count / eval_duration` measures generation tokens/sec, not end-to-end speed; API durations are nanoseconds. [Ollama chat API](https://docs.ollama.com/api/chat)

The **whole case**, including both switch turns, has a 120-second deadline. A separate request process enforces that deadline even when a socket trickles data. On timeout, the socket/worker closes and the attempt fails; the harness halts subsequent generation because that does not prove the daemon stopped computing. Inspect `ollama ps` and stop a lingering model before rerunning. Remaining trials are unrun, not invented failures. Process teardown can add a small amount beyond the inference deadline.

`results.json` includes raw visible model answers, per-turn scores, timings, token counts, model metadata, configuration and input hashes. It does not save hidden thinking. `results.md` has one model × case table. Medians include all attempted trials, including measured failures, and exclude unattempted ones. Accuracy and parsing have a planned denominator of three; a completely blocked row says `N/A (0/3 run)`. Exit code 2 means blocked/partial execution; 0 means all planned trials were attempted, **not** that a model passed.

## Fixtures and exact answers

Hand-transcribed long-form rows: Samsung has six statement metrics × three years (18 rows); NAVER has five × three (15 rows). Each observation has its own fiscal period and source. `연구개발비` is deliberately absent. Absence from this fixture is not a claim about its absence from a company's complete filings.

Samsung values come from the Korean consolidated income statements in the issuer's [2023 audit report, PDF page 12](https://images.samsung.com/kdp/ir/financial-info/2023/2023_con_quarter04_all.pdf) and [2022 audit report, PDF page 11](https://images.samsung.com/kdp/ir/financial-info/2022/2022_con_quarter04_all.pdf). The older report supplies the 2021 comparative. Amounts are reported in 백만원.

NAVER values and labels come from its [2023 Integrated Report, PDF page 162, 연결포괄손익계산서](https://kind.krx.co.kr/external/2024/06/26/000486/20240625001176/NAVER_Integrated_Report_2023_ver3.pdf). Its revenue line is `영업수익`, with an explicit `매출액` alias. It does not have the manufacturing-style gross-profit rows used by Samsung; those are not fabricated. The source reports 원; each value is divided **exactly** by 1,000,000 to match the benchmark's 백만원 unit. Expense parentheses retain their negative sign. Raw amounts and units stay in the fixture for audit, but the model sees only normalized rows. NAVER's unusually large 2021 net income is transcribed as reported, not treated as recurring operating performance.

Labels remove typesetting spaces and Roman numeral prefixes. The fixtures preserve Korean statement wording, but **DART viewer label parity and regulator receipt IDs have not been independently verified**. NAVER's integrated report is a primary issuer publication hosted on KIND, not a DART business-report link. These fixtures are sufficient for table-only inference experiments, not for shipping the promised original-filing provenance catalog or proving DART extraction quality.

Expected revenue: Samsung 2023 `258935494`, 2022 `302231360`; percentage `(258935494 - 302231360) / 302231360 * 100`, rounded half up to `-14.33`. NAVER 2023 revenue: `9670643.576585`. All reported values use 백만원. Cases contain independent explicit expected values; fixture drift fails validation before inference.

## Scoring and limitations

Strict JSON parsing rejects code fences, duplicate keys and non-JSON constants. Schema checks require both answer strings, exact keys, and typed refusal fields. Reported facts are matched by label, period, unit, decimal value **and complete source**, allowing figure reordering but no extra figures. Decimal-equivalent string formatting is accepted; JSON numbers violate the prompt's string contract. A calculation must have the correct value, permitted arithmetic expression, and ordered inputs with original sources. The `inputs` field extends the example calculation object to satisfy the requirement to show each operand.

The numeric audit records digit-based numeric occurrences in all visible output strings and values, including prose. Numbers absent from the supplied table/question are recorded as novel. A correctly validated derived value is exempt from hallucination counting; its formula constant `100` is permitted only inside that verified formula. The remaining unsupported occurrences are quoted verbatim in report notes. Wrong-source and wrong-period facts fail exact scoring even if their number appears elsewhere in the table.

The missing case requires refusal, an explanation, and empty figures/calculations. Any supplied unrelated figure or financial amount in a refusal is also a violation, including zero. **An invented missing-case amount disqualifies a model regardless of speed.** The refusal gate is reported separately from comparison performance; blocked, failed or incomplete trials cannot establish a pass.

This is a numeric/provenance diagnostic, not a semantic verifier. It cannot reliably detect spelled-out invented quantities, a wrong factual claim with no digits, an amount attached to the wrong concept only in prose, or poor Korean/English translations. Read both answer strings manually before selecting a model. A number merely appearing somewhere in the supplied evidence does not prove a narrative claim is supported. Three trials of three cases are a smoke benchmark, not statistical confidence or a production release bar. Fixed temperature/seed does not guarantee identical outputs across runtimes and machines.

The fixtures deliberately bypass PDF/HTML parsing, extraction, source-link checks and evidence search. They cannot establish that a 7–8B model can read Korean financial tables, or that the whole application fits in 16GB RAM. If the full prompt exceeds context, generation is truncated, or a model cannot disable thinking, record the failure and inspect metadata; do not silently increase resources or enable cloud fallback. The product should independently compute and validate arithmetic even if a model passes this diagnostic.

## Harness verification

```sh
python3 -m unittest discover -s bench/tests -v
```

Tests cover calculation exemptions, wrong operands/sources/periods/units, invented prose amounts, false refusals, JSON errors, company-switch history, local-model rejection, a real process deadline, and report generation with mocked API responses. Test answers are never written as model benchmark results.

## September 7 verified-pilot extension

[Measured setup and findings](runs/2026-09-07/README.md) records the installed runtime, original diagnostic, and the verified-pilot experiment. Ollama was installed through Homebrew after the owner authorized this feasibility check. No account or login was used. Model downloads are network acquisition; inference uses local weights. `~/.ollama/server.json` also disables cloud support persistently. No login/startup service was installed.

From the repository root, start the controlled daemon in a separate terminal:

```sh
./bench/serve.sh
```

With the already installed models and project virtual environment, run both suites serially:

```sh
.venv/bin/python bench/run.py && .venv/bin/python bench/pilot.py
```

The second suite is intentionally separate: it uses the audit's complete 15-fact verified catalog, exact evidence-ID selection, and deterministic arithmetic. It tests Korean/English requests, company switching, missing evidence, pressure to invent zero or reuse the wrong year, currency incompatibility, unsupported separate statements, and clarification. It does not ask the model to copy full source objects or financial values. Code resolves IDs back to the pinned source; model prose must contain no financial amounts. This is an experiment, not the production router: scoring uses an independent expected intent per case, which the model never receives. Production must validate inferred intent without that test oracle. Two-turn cases retain the actual first response even when it fails scoring; no corrected answer is injected into history.

`pilot-results/` contains three repetitions per case: first after a confirmed unload and two with the model kept warm. Cold here means load-inclusive with possible OS cache; no caches are purged. The complete switch conversation shares the 120-second case deadline. The model is unloaded between cases and after the suite. Per-trial memory samples record system swap/pressure, Ollama process RSS and `/api/ps` allocations. Process RSS is not the complete unified-memory footprint; pressure and swap include other applications. All runs are serial with one loaded model. Server settings are in `serve.sh`; neither suite changes a server started elsewhere.

Use `BENCH_OUTPUT_DIR=bench/runs/<name>` for a separate original-diagnostic report and `PILOT_OUTPUT_DIR=bench/runs/<name>` for a separate pilot report. Both paths must stay inside `bench`. Keep previous trials when changing a prompt, runtime or configuration. A completed suite means all calls were attempted, not that the candidate passed. The original table fixtures remain unchanged so results stay comparable; their older issuer-publication provenance is not silently upgraded to the regulator-verified pilot.

## Intent-only survivor experiment

The [final September 7 findings](runs/2026-09-07/README.md) supersede any earlier unrun status: Qwen 8B fabricated an absent amount under pressure and is disqualified. Gemma is the provisional candidate only with the smaller intent-only contract. Run that experiment with:

```sh
.venv/bin/python bench/intent.py
```

It writes `intent-results/results.json` and `results.md`; `INTENT_OUTPUT_DIR=bench/runs/<name>` preserves a separate run. The default is `gemma4:e4b`. It uses JSON Schema output, context 4096, output cap 256, temperature zero, seed 42, disabled thinking, and serial cold/warm measurements. The model receives the question and accepted intent context, with no financial values. Code selects the source-bound rows, applies missing-evidence/basis/currency checks, performs Decimal arithmetic and produces both financial answer sentences. This follows [Ollama's structured-output API](https://docs.ollama.com/capabilities/structured-outputs); the client still validates every field.

All three suites can be run serially with `.venv/bin/python bench/run.py && .venv/bin/python bench/pilot.py && .venv/bin/python bench/intent.py`. This reruns the rejected configurations for comparison; it does not reinstate Qwen as a candidate. Keep previous output directories when changing anything.

To check the captured September 7 artifacts without calling any model, run `.venv/bin/python bench/verify_results.py`. The [source archive](runs/2026-09-07/harness-source.zip) retains the exact benchmark scripts, prompts and fixtures used during measurement. The report separates strict numeric/intent scores from the [semantic review](runs/2026-09-07/semantic-review.json): both models could select correct IDs and still write a false trend sentence.

## Shared application policy

New intent-only runs use `slice/financial.py`, the same deterministic financial policy as the application. The extraction preserves the verified coverage and keeps model execution outside that module. Recorded September 7 results and `runs/2026-09-07/harness-source.zip` retain the original experiments; use that archived source to reproduce their exact implementation.
