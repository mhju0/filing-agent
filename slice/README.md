# Filing Agent local application

Korean/English questions over a pinned, verified filing collection. Gemma interprets the question on the Mac; deterministic code selects evidence, computes changes and supplies the financial wording. The browser displays the original filing units and preserves sources with saved answers.

The public experience is a static recording. It has no question endpoint, login or connection to the owner's Mac.

## Run locally

Requirements: Apple Silicon Mac, 16 GiB RAM tested, Python 3.11, Node 24, PostgreSQL 16 command-line tools, Ollama 0.33.3 and the qualified local `gemma4:e4b` weights. Runtime and model digest changes require requalification. Package/model installation needs internet; ordinary snapshot queries use local services.

From the repository root:

```sh
python3.11 -m venv .venv
.venv/bin/pip install -r slice/requirements.lock
npm ci --prefix slice/web
npm run build --prefix slice/web
./slice/scripts/database.sh
```

Before the first run, install the stated Ollama version and download the local model with `ollama pull gemma4:e4b`. The tag must resolve to digest `c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb`; the app verifies it on every request. No Ollama account or hosted model is used. Stop any existing Ollama server before using this project's controlled launcher.

Set `disable_ollama_cloud` to `true` in `~/.ollama/server.json`, preserving other settings. The app requires this setting in addition to the launcher's `OLLAMA_NO_CLOUD=1`. Package/model downloads are the online installation step; model updates require rerunning qualification.

Start Ollama in one terminal, then the app in another:

```sh
./bench/serve.sh
```

```sh
./slice/scripts/serve.sh
```

Open **http://127.0.0.1:8765**. The exact loopback host is part of the browser security boundary. Do not bind these services to a public address or run multiple application workers.

The database script creates a separate cluster at `.local/slice-postgres`, port `55439`, database `filing_agent_slice`, role `filing_agent`. It never opens Filing Digest's database. Local cluster connections use trust authentication on loopback; this is a single-owner development machine boundary, not protection against other processes running as local users. No startup service or account is installed.

To stop the app and model server, press Ctrl-C in their terminals. Stop the Agent database with:

```sh
pg_ctl -D "$PWD/.local/slice-postgres" stop
```

## Evidence and conversations

Supported: consolidated revenue, operating income and as-reported net income for Samsung FY2022/2023, NAVER FY2023 and Microsoft FY2023/2024. Microsoft fiscal years end in June. The collection is historical and does not claim an exhaustive search of later amendments. R&D is outside this verified statement collection; it is not absent from the full Samsung filing.

Missing company/year/metric prompts a clarification. Pending clarification is persisted separately from accepted context. Unknown values never become zero. Compatible annual changes use Decimal and retain source-bound operands. Available figures remain visible when another period or the requested calculation is unavailable.

Save freezes the investigation. Continue creates a new investigation with its original context, turns and pinned evidence. Refresh creates a new investigation using the current approved snapshot and prefills the previous question for deliberate resubmission. With the present single snapshot, dates and numbers can remain identical; Refresh does not imply that new filings were downloaded.

Edit starts a new investigation. Changing interface language preserves earlier local answer wording. Ordinary conversations expire after thirty idle days; saved investigations remain until deleted. Deletion does not erase copies in explicit exports or macOS backups.

Three real graph stages are shown: interpretation; evidence resolution and arithmetic; answer persistence. There is no invented filing-download or extraction progress. Completed steps persist in PostgreSQL. After a process interruption, the owner can retry once; completed step outputs are reused and the interrupted step starts from its persisted inputs. This is explicit step recovery, not token-level generation resumption or a native tool-calling claim.

Cancellation terminates the client worker, requests model unload and checks the local runtime. An unconfirmed stop blocks further inference until the controlled runtime is reset. All model requests are serial.

## Private data commands

These commands operate locally and never publish a file:

```sh
.venv/bin/python -m slice.backup backup /absolute/path/filing-agent-private.json
.venv/bin/python -m slice.backup restore /absolute/path/filing-agent-private.json
.venv/bin/python -m slice.backup clear-diagnostics
```

Backups contain private questions and answers. They omit raw model diagnostics, use file mode 0600, and refuse to overwrite a file. Restore creates new investigation IDs and preserves existing records. Restoring can reintroduce data previously deleted. Backup checksums detect accidental changes, not malicious edits by someone who can recompute the checksum.

Normal application execution retains model/config/timing metadata and interpreted intent, without raw model output. An explicit API `diagnostics: true` opt-in captures the observable intent JSON for that turn. It excludes hidden reasoning and credentials. Raw diagnostic output expires after 24 hours, with cleanup at startup and every minute while the app runs; external backup copies and stopped applications cannot promise timed physical erasure. Evaluation artifacts are separately retained evidence, not ordinary conversations.

## Verify and export

```sh
.venv/bin/python -m unittest discover -s slice/tests -v
npm run build --prefix slice/web
node slice/scripts/verify-browser.mjs
```

Install browser verification tools with `npm ci --prefix verification`. Verification uses Playwright, Chrome and axe; it has no runtime role in the application.

Only explicitly selected, saved, fully completed real investigations can be exported:

```sh
.venv/bin/python -m slice.export INVESTIGATION_ID_1 INVESTIGATION_ID_2 INVESTIGATION_ID_3 --output slice/replay
python3 -m http.server 4176 --bind 127.0.0.1 --directory slice/replay
```

The export directory must be new. It contains only bundled UI assets and selected sanitized recording data. It excludes private history, raw model messages, diagnostics, credentials and private planning. Source navigation is an intentional external action; replay controls use static assets only.

## Public release evidence

The deployed project notes link to the three real recordings, evaluation summary, scenario definitions and source archive. The archive is a deliberate source distribution without private planning or Git history. No open-source license is granted for original project code in this release. The bundled Pretendard font includes its license; dependencies and model weights have their own license terms.
