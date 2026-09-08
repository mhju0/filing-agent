#!/usr/bin/env python3
"""Run serial, local-only Ollama trials. No downloads or cloud fallback."""

import hashlib
import json
import multiprocessing
import os
import platform
import re
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

if __package__:
    from .memory_monitor import Monitor
    from .scoring import figure_from_row, score, expected_figures
else:
    from memory_monitor import Monitor
    from scoring import figure_from_row, score, expected_figures

ROOT = Path(__file__).resolve().parent
BASE_URL = "http://127.0.0.1:11434"
RUNS = 3
TIMEOUT = 120
OPTIONS = {"temperature": 0, "num_ctx": 8192, "num_predict": 2048, "seed": 42}


def api(method, path, payload=None, timeout=5):
    with requests.Session() as session:
        session.trust_env = False
        response = session.request(method, BASE_URL + path, json=payload,
                                   timeout=timeout, allow_redirects=False)
        if 300 <= response.status_code < 400:
            raise RuntimeError("Redirect refused: benchmark only permits loopback Ollama")
        response.raise_for_status()
        return response.json()


def chat_worker(connection, payload, timeout):
    try:
        connection.send({"response": api("POST", "/api/chat", payload, timeout)})
    except Exception as exc:
        connection.send({"error": f"{type(exc).__name__}: {exc}"})
    finally:
        connection.close()


def timed_chat(payload, timeout, worker=chat_worker):
    context = multiprocessing.get_context("spawn")
    reader, writer = context.Pipe(duplex=False)
    process = context.Process(target=worker, args=(writer, payload, timeout), daemon=True)
    started = time.monotonic()
    process.start()
    writer.close()
    try:
        if reader.poll(max(0, timeout - (time.monotonic() - started))):
            try:
                result = reader.recv()
            except EOFError:
                result = {"error": "Chat worker exited without a response"}
        else:
            result = {"error": f"Case exceeded {TIMEOUT}s wall-clock ceiling", "timeout": True}
    finally:
        reader.close()
        if process.is_alive():
            process.terminate()
        process.join(timeout=1)
        if process.is_alive():
            process.kill()
            process.join(timeout=1)
    result["wall_seconds"] = time.monotonic() - started
    return result


def local_model_info(name):
    info = api("POST", "/api/show", {"model": name})
    remote_markers = [info.get("remote_host"), info.get("remote_model"),
                      info.get("model_info", {}).get("remote_host"),
                      info.get("model_info", {}).get("remote_model")]
    if "cloud" in name.lower() or any(remote_markers):
        raise ValueError("Cloud/remote model rejected; local inference has no exceptions")
    if not info.get("model_info", {}).get("general.architecture"):
        raise ValueError("Could not verify local model architecture; refusing inference")
    if re.search(r"(?im)^FROM\s+.*(?:https?://|:.*cloud)", info.get("modelfile", "")):
        raise ValueError("Remote model reference rejected")
    return {key: info.get(key) for key in ("details", "model_info", "capabilities")}


def select_models(installed):
    if os.environ.get("MODELS", "").strip():
        return list(dict.fromkeys(re.split(r"[,\s]+", os.environ["MODELS"].strip())))
    exaone = [name for name in installed if "exaone" in name.lower()]
    return list(dict.fromkeys(["qwen3:8b", "gemma4:e4b", *sorted(exaone)]))


def run_trial(model, case, fixtures, system, thinking):
    started = time.monotonic()
    messages = [{"role": "system", "content": system}]
    trial = {"turns": [], "accuracy": False, "json_parse_success": False,
             "invented_numbers": [], "refusal_violation": False}
    for turn in case["turns"]:
        remaining = TIMEOUT - (time.monotonic() - started)
        if remaining <= 0:
            trial.update(error="Case deadline exhausted", timeout=True)
            break
        fixture = fixtures[turn["fixture"]]
        table = {"company": fixture["company"], "currency": fixture["currency"],
                 "basis": fixture["basis"], "metric_aliases": fixture["metric_aliases"],
                 "rows": [figure_from_row(row) for row in fixture["rows"]]}
        messages.append({"role": "user", "content": "TABLE:\n" + json.dumps(table, ensure_ascii=False)
                         + "\nQUESTION:\n" + turn["question"]})
        payload = {"model": model, "messages": messages, "format": "json", "stream": False,
                   "options": OPTIONS, "keep_alive": 0}
        if thinking:
            payload["think"] = False
        response = timed_chat(payload, remaining)
        record = {"question": turn["question"], "wall_seconds": response["wall_seconds"]}
        if "error" in response:
            record.update({key: response[key] for key in ("error", "timeout") if key in response})
            trial["turns"].append(record)
            trial.update({key: response[key] for key in ("error", "timeout") if key in response})
            break
        body = response["response"]
        content = body.get("message", {}).get("content", "")
        if not isinstance(content, str):
            content = ""
        record["content"] = content
        record["metrics"] = {key: body.get(key) for key in (
            "total_duration", "load_duration", "prompt_eval_count", "prompt_eval_duration",
            "eval_count", "eval_duration", "done", "done_reason")}
        duration, count = body.get("eval_duration"), body.get("eval_count")
        record["tokens_per_second"] = count * 1e9 / duration if duration and count is not None else None
        record["score"] = score(content, fixture, turn["expected"], turn["question"])
        if body.get("done") is not True or body.get("done_reason") == "length":
            record["score"]["accuracy"] = False
            record["error"] = "Generation incomplete or token limit reached"
        trial["turns"].append(record)
        trial["invented_numbers"].extend(record["score"]["invented_numbers"])
        trial["refusal_violation"] |= record["score"]["refusal_violation"]
        # Preserve the actual first answer, even when it is incorrect; never inject the oracle.
        messages.append({"role": "assistant", "content": content})
    complete = len(trial["turns"]) == len(case["turns"])
    trial["accuracy"] = complete and all(t.get("score", {}).get("accuracy", False) for t in trial["turns"])
    trial["json_parse_success"] = complete and all(t.get("score", {}).get("json_parse_success", False)
                                                   for t in trial["turns"])
    trial["wall_seconds"] = time.monotonic() - started
    return trial


def markdown(result):
    lines = ["# Local model benchmark", "", f"Recorded: {result['created_at']}", "",
             ("Status: " + result["status"] + ". " + result.get("preflight_error", "")).rstrip(), "",
             "| Model | Case | Median seconds | Accuracy | Parse rate | Hallucinations | Notes |",
             "| --- | --- | ---: | --- | --- | ---: | --- |"]
    for entry in result["results"]:
        runs = entry["runs"]
        median = f"{statistics.median(r['wall_seconds'] for r in runs):.2f}" if runs else "N/A"
        correct = f"{sum(r['accuracy'] for r in runs)}/{RUNS}" if runs else "N/A (0/3 run)"
        parsed = f"{sum(r['json_parse_success'] for r in runs)}/{RUNS}" if runs else "N/A (0/3 run)"
        invented = [number for run in runs for number in run["invented_numbers"]]
        notes = [entry.get("reason", "")]
        notes += [run["error"] for run in runs if run.get("error")]
        notes += [turn["error"] for run in runs for turn in run["turns"] if turn.get("error")]
        if invented:
            notes.append("Invented numbers: " + ", ".join('`' + n + '`' for n in invented))
        notes.append("Refusal gate: " + result["model_verdicts"].get(entry["model"], "not evaluated"))
        note = "; ".join(dict.fromkeys(filter(None, notes))).replace("|", "\\|").replace("\n", " ")
        count = str(len(invented)) if runs else "N/A"
        lines.append(f"| {entry['model']} | {entry['case']} | {median} | {correct} | {parsed} | {count} | {note} |")
    lines += ["", "Three trials per case. Switch accuracy and parsing require both turns to pass; its time is the two-turn total.",
              "Median includes attempted failures/timeouts, excludes unattempted runs. Each case has a 120s wall deadline.",
              "Hallucinations count unsupported numeric occurrences (including prose), not unique numbers. Correct, validated calculations are exempt.",
              "Refusal violations also include returning an unrelated supplied figure. See results.json for raw visible answers, sources, per-turn metrics and gate reasons.",
              "Times include model loading: keep_alive=0 unloads after every turn. No warmup, no parallel generation. Runtime may retain OS file cache.",
              "No model is selected automatically. This is a structured-table diagnostic, not a DART extraction or bilingual semantic-quality certification.", ""]
    return "\n".join(lines)


def save(result):
    destination = Path(os.environ.get("BENCH_OUTPUT_DIR", str(ROOT))).resolve()
    if not destination.is_relative_to(ROOT):
        raise ValueError("BENCH_OUTPUT_DIR must stay within bench")
    destination.mkdir(parents=True, exist_ok=True)
    for filename, content in (("results.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n"),
                              ("results.md", markdown(result))):
        temporary = destination / (filename + ".tmp")
        temporary.write_text(content)
        temporary.replace(destination / filename)


def main():
    cases = json.loads((ROOT / "cases.json").read_text())
    fixtures = {name: json.loads((ROOT / "fixtures" / name).read_text())
                for name in {turn["fixture"] for case in cases for turn in case["turns"]}}
    for case in cases:
        for turn in case["turns"]:
            expected_figures(fixtures[turn["fixture"]], turn["expected"])
    inputs = [ROOT / "cases.json", ROOT / "prompts/system.txt", *sorted((ROOT / "fixtures").glob("*.json"))]
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "status": "running",
              "machine": {"system": platform.system(), "machine": platform.machine(), "python": platform.python_version()},
              "config": {"base_url": BASE_URL, "runs": RUNS, "case_timeout_seconds": TIMEOUT,
                         "options": OPTIONS, "keep_alive": 0, "stream": False, "format": "json",
                         "thinking": "disabled when supported", "execution": "serial"},
              "input_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in inputs},
              "installed_models": [], "model_metadata": {}, "model_verdicts": {}, "results": []}
    try:
        installed = api("GET", "/api/tags")["models"]
        result["installed_models"] = installed
        result["ollama_version"] = api("GET", "/api/version").get("version")
        installed_by_name = {item["name"]: item for item in installed}
    except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
        installed_by_name = {}
        result["preflight_error"] = f"Local Ollama preflight failed at {BASE_URL}: {type(exc).__name__}"
        result["preflight_detail"] = str(exc)
    models = select_models(installed_by_name)
    result["requested_models"] = models
    system = (ROOT / "prompts/system.txt").read_text()
    halt_reason = None
    for model in models:
        reason = halt_reason or result.get("preflight_error")
        if not reason and model not in installed_by_name:
            reason = "Exact tag is not installed; no pull was attempted"
        if not reason:
            try:
                if installed_by_name[model].get("size", 0) <= 0:
                    raise ValueError("No local model weights reported")
                result["model_metadata"][model] = local_model_info(model)
            except (requests.RequestException, RuntimeError, ValueError, KeyError) as exc:
                reason = f"Model preflight rejected: {exc}"
        result["model_verdicts"][model] = "not evaluated"
        for case in cases:
            entry = {"model": model, "case": case["id"], "runs": []}
            result["results"].append(entry)
            if reason or halt_reason:
                entry["reason"] = reason or halt_reason
                save(result)
                continue
            for index in range(RUNS):
                print(f"{model} / {case['id']} / {index + 1}/{RUNS}", flush=True)
                info = result["model_metadata"][model]
                with Monitor() as monitor:
                    trial = run_trial(model, case, fixtures, system, "thinking" in (info.get("capabilities") or []))
                trial["memory"] = monitor.summary()
                entry["runs"].append(trial)
                if case["id"] == "missing":
                    if trial["invented_numbers"] or trial["refusal_violation"]:
                        result["model_verdicts"][model] = "DISQUALIFIED: fabricated missing-metric answer"
                    elif result["model_verdicts"][model].startswith("DISQUALIFIED"):
                        pass
                    elif all(r["accuracy"] for r in entry["runs"]) and len(entry["runs"]) == RUNS:
                        result["model_verdicts"][model] = "passed 3/3 missing trials; inspect bilingual prose manually"
                    else:
                        result["model_verdicts"][model] = "not passed or incomplete"
                save(result)
                if trial.get("timeout"):
                    halt_reason = "Stopped after deadline: socket closed, but daemon cancellation is unverified; inspect ollama ps before rerunning"
                    entry["reason"] = halt_reason
                    break
    attempted = sum(len(entry["runs"]) for entry in result["results"])
    planned = len(models) * len(cases) * RUNS
    result["status"] = "blocked" if not attempted else ("complete" if attempted == planned else "partial")
    result["attempted_trials"] = attempted
    result["planned_trials"] = planned
    save(result)
    destination = Path(os.environ.get("BENCH_OUTPUT_DIR", str(ROOT))).resolve()
    print(f"{result['status']}: {attempted}/{planned} trials; {destination / 'results.md'}")
    return 0 if result["status"] == "complete" else 2


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
