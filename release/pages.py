"""Public project notes assembled only from approved application and audit evidence."""

import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

COPY = {
    "en": {
        "title": "Evidence before answers",
        "back": "Return to recorded investigations",
        "lead": "A local research workspace for asking follow-up questions about a small, verified set of Korean and US filing figures. This site replays real runs without connecting to the owner’s Mac.",
        "story": "Why build it?",
        "story_body": "Filing Digest is the sister project: it handles filing ingestion, retrieval and the iOS reader. Agent carries that evidence discipline into follow-up questions and saved investigations. Its pinned collection contains nine audited Digest facts and six separately verified regulator supplements. Questions run against that snapshot without calling Digest’s live API or Solar service. The recorded replay shows the actual results, sources and recovery design.",
        "boundary": "Where the model stops",
        "boundary_body": "Gemma interprets the company, metric, fiscal year, basis and action. It never receives a filing or writes the financial answer. Code checks the intent against explicit question/context constraints, selects source-bound facts, calculates compatible changes with Decimal and supplies Korean/English wording. Missing evidence stays missing. Business-cause explanations are outside this collection.",
        "flow": "Question → local intent interpretation → validated evidence and arithmetic → persisted answer → selected static recording",
        "state": "Preserving a result",
        "state_body": "FastAPI serves one local browser origin. LangGraph runs three observable stages with PostgreSQL checkpoints; application rows retain each completed step and source snapshot. Saving freezes an investigation. Continue copies its original evidence and context into a new investigation; Refresh starts a new one on the currently approved snapshot. A restart marks unfinished work interrupted. One explicit retry reuses completed steps. Cancellation must confirm that local inference stopped. Completion includes durable timing metadata. If storage fails, Retry storage preserves the verified result without repeating inference; closing the local app can lose unstored results.",
        "results": "Historical release evaluation",
        "results_body": "The architecture refactor passed 17 application tests and 31 benchmark tests; 1,800 financial outputs were unchanged across extraction. In the original release evaluation, forty execution-held-out scenarios ran three times: 20 Korean and 20 English per trial, 120/120 expected task outcomes across 138 actual turns. Each language/trial includes ten supported answers and ten withholding or clarification cases. Source/value audit found no mismatches. These are agent-authored paraphrases of known task families, not an independent test of arbitrary financial language.",
        "timing": "On an M1 Pro with 16 GiB RAM: median 2.96 seconds, observed p95 3.19 seconds, maximum 9.78 seconds per turn. Mostly warm; first turn includes loading. Concurrent application/browser profiling observed normal and warning memory pressure, with existing system swap. This does not establish an 8 GiB support claim.",
        "failures": "Failures that changed the design",
        "failures_body": "An earlier Qwen run invented zero for a missing R&D figure; it was disqualified. Gemma initially guessed a company for a company-free question. An English company switch was safely blocked, and an SEC adapter assumed a section field that was absent. Retained development failures led to explicit context guards, a code-owned financial answer and honest source metadata. The final score describes the guarded application, not the model alone.",
        "limits": "Coverage and limits",
        "limits_body": "Fifteen verified facts: consolidated revenue, operating income and as-reported net income for Samsung FY2022–2023, NAVER FY2023 and Microsoft FY2023–2024. Microsoft fiscal years end in June. R&D is absent from this verified collection, not necessarily from the full filings. Later amendments have not been exhaustively reviewed. DART browser navigation and all nine Korean source amounts were checked. SEC blocked automated browser navigation; its original URLs remain available with that limitation disclosed.",
        "security": "Local execution and public data",
        "security_body": "Inference uses pinned Ollama 0.33.3 and local gemma4:e4b weights, with cloud disabled. The held-out run blocked application/model outbound traffic except localhost. The single-owner Mac uses a separate loopback PostgreSQL cluster. Browser mutations require the exact local host/origin and a session token. This does not defend against a compromised local account. Ordinary investigations expire after 30 idle days; saved results remain until deleted. Private backups are explicit and exclude raw model diagnostics.",
        "public_body": "The public artifact contains selected captured turns, source excerpts, static assets and engineering materials. It has no question endpoint, sign-in, analytics or connection to the Mac. Static hosting does not demonstrate production cloud operations. Installation and deliberate source navigation require internet; snapshot queries are local.",
        "video": "Watch an actual local run",
        "video_body": "An unedited browser recording asks for Samsung FY2023 revenue, then follows up with a comparison to FY2022. The pauses are real execution time. Captions and the two-step transcript describe the same run.",
        "video_step_one": "Ask for Samsung FY2023 revenue and inspect the reported figure.",
        "video_step_two": "Follow up with FY2022 and compare source-bound values.",
        "replay_link": "Inspect the interactive recorded investigations",
        "verification": "Latest verification record",
        "materials": "Inspect and run",
        "source": "Download application source (ZIP)",
        "setup": "Local setup and operating notes",
        "evaluation": "Evaluation summary (JSON)",
        "cases": "Evaluation scenarios (JSON)",
        "license": "The archive excludes private planning and Git history. No open-source license is granted for original project code in this release. Pretendard font license is included. Model and dependency licenses apply separately.",
    },
    "ko": {
        "title": "답변보다 먼저 확인할 근거",
        "back": "녹화된 조사로 돌아가기",
        "lead": "한국·미국 기업 공시에서 검증한 일부 수치를 후속 질문으로 조사하는 로컬 작업 공간입니다. 이 사이트에서는 소유자의 Mac에 연결하지 않고 실제 실행을 살펴볼 수 있습니다.",
        "story": "이 프로젝트를 만든 이유",
        "story_body": "Filing Digest는 공시 데이터 기반을 담당하는 동반 프로젝트입니다. 최신 기간 요약만으로는 과거 연도를 오가는 대화를 지원할 수 없습니다. Agent는 Digest의 기반과 DART·EDGAR 원문을 별도로 검증한 고정 수치 모음을 사용합니다. 여기에 대화 맥락, 정확한 계산, 결과 보존, 중단 후 복구를 더했습니다. 공개 리플레이는 개인 Mac을 노출하지 않고 이 동작을 확인할 수 있게 합니다.",
        "boundary": "모델이 담당하는 범위",
        "boundary_body": "Gemma는 회사, 지표, 회계연도, 연결·별도 기준, 요청 동작을 해석합니다. 공시 원문을 읽거나 재무 답변을 작성하지 않습니다. 코드는 명시된 질문과 기존 맥락에 맞는지 확인하고, 원문 근거가 연결된 수치를 선택하며, 비교 가능한 값만 Decimal로 계산한 뒤 한국어·영어 문장을 제공합니다. 확인하지 못한 값은 비워 둡니다. 사업상 원인 설명은 이 수치 모음의 범위 밖입니다.",
        "flow": "질문 → 로컬 의도 해석 → 근거 검증·계산 → 답변 저장 → 선택한 실행의 정적 녹화본",
        "state": "원래 결과를 보존하는 방법",
        "state_body": "FastAPI는 하나의 로컬 브라우저 출처를 제공합니다. LangGraph는 세 개의 실제 처리 단계를 실행하고 PostgreSQL에 체크포인트를 저장합니다. 앱 데이터에는 완료한 단계와 근거 스냅샷이 남습니다. 저장한 조사는 고정됩니다. 이어하기는 원래 근거와 맥락을 새 조사에 복사하고, 새 근거로 시작하기는 현재 승인된 스냅샷으로 새 조사를 만듭니다. 재시작 시 미완료 작업은 중단으로 표시합니다. 명시적 재시도는 한 번이며 완료한 단계를 재사용합니다. 취소는 로컬 추론 중단을 확인해야 완료됩니다. 결과와 실행 시간이 영구 기록된 뒤에 완료로 표시합니다. 기록 실패 시 검증된 결과를 추론 없이 다시 기록할 수 있습니다. 로컬 앱을 종료하면 미기록 결과는 사라질 수 있습니다.",
        "results": "기존 릴리스 평가",
        "results_body": "구조 개선 후 앱 테스트 17개와 벤치마크 테스트 31개를 통과했고, 재무 정책 분리 전후 1,800개 출력이 일치했습니다. 기존 릴리스 평가에서는 실행 보류한 40개 시나리오를 세 차례 측정했습니다. 매회 한국어 20개·영어 20개, 총 120회 시나리오의 기대 결과가 모두 일치했습니다. 실제 대화 턴은 138개입니다. 언어별·회차별로 정상 답변 10개와 수치 보류 또는 추가 확인 10개가 포함됩니다. 원문 수치·출처 대조에서 불일치는 없었습니다. 개발과 같은 작업 유형을 바꿔 표현한 에이전트 작성 문제이며, 임의의 금융 질문에 대한 독립 평가가 아닙니다.",
        "timing": "M1 Pro·16 GiB RAM에서 턴당 중앙값 2.96초, 관측 p95 3.19초, 최댓값 9.78초였습니다. 대부분 모델이 로드된 상태이며 첫 턴에는 로딩이 포함됩니다. 앱·브라우저 동시 측정에서는 정상 및 경고 메모리 압력과 기존 시스템 스왑을 관측했습니다. 8 GiB 지원을 입증한 결과는 아닙니다.",
        "failures": "실패에서 바뀐 설계",
        "failures_body": "이전 Qwen 실험은 없는 연구개발비를 0으로 만들어 후보에서 제외했습니다. Gemma도 회사가 없는 질문에 회사를 추측했습니다. 영어 회사 전환은 검증 단계에서 차단됐고, SEC 어댑터는 없는 section 필드를 가정해 실패했습니다. 이 개발 실패를 보존하고 명시적 맥락 검증, 코드 기반 재무 답변, 실제 제공되는 원문 메타데이터를 반영했습니다. 최종 점수는 모델 단독이 아닌 검증 로직을 포함한 앱의 결과입니다.",
        "limits": "지원 범위와 한계",
        "limits_body": "검증 수치는 15개입니다. 삼성전자 FY2022–2023, NAVER FY2023, Microsoft FY2023–2024의 연결 매출액·영업이익·공시된 당기순이익을 지원합니다. Microsoft 회계연도는 6월에 끝납니다. 연구개발비는 검증 모음에 없으며, 공시 전체에 없다는 뜻은 아닙니다. 이후 정정 공시를 전수 조사하지 않았습니다. DART 브라우저 이동과 한국 공시 수치 9개를 확인했습니다. SEC는 자동 브라우저 접근을 차단했으며, 원문 URL과 이 제한을 함께 표시합니다.",
        "security": "로컬 실행과 공개 데이터",
        "security_body": "Ollama 0.33.3과 고정된 gemma4:e4b 로컬 가중치를 사용하고 클라우드를 비활성화했습니다. 보류 평가 시 앱·모델의 localhost 외 외부 통신을 차단했습니다. 단일 소유자의 Mac에서 별도 루프백 PostgreSQL 클러스터를 사용합니다. 브라우저 변경 요청에는 정확한 로컬 호스트·출처와 세션 토큰이 필요합니다. 이미 침해된 로컬 계정에 대한 방어는 아닙니다. 일반 조사는 30일 미사용 후 만료하고, 저장한 결과는 삭제할 때까지 보존합니다. 명시적으로 만드는 개인 백업에는 원시 모델 진단 출력을 넣지 않습니다.",
        "public_body": "공개 파일은 선택한 실제 대화, 원문 발췌, 정적 자산, 기술 자료로 구성됩니다. 질문 API·로그인·분석 추적·Mac 연결은 없습니다. 정적 호스팅으로 프로덕션 클라우드 운영 경험을 주장하지 않습니다. 설치와 사용자가 여는 원문 링크에는 인터넷이 필요하며, 고정 근거에 대한 질문은 로컬에서 처리합니다.",
        "video": "로컬 앱의 실제 실행 보기",
        "video_body": "삼성전자 FY2023 매출액을 묻고 FY2022와 비교하는 후속 질문까지 담은 무편집 브라우저 녹화입니다. 대기 시간은 실제 실행 시간입니다. 자막과 두 단계 설명은 같은 실행을 담고 있습니다.",
        "video_step_one": "삼성전자 FY2023 매출액을 묻고 공시 수치를 확인합니다.",
        "video_step_two": "FY2022를 후속 질문으로 요청하고 원문 근거가 연결된 수치를 비교합니다.",
        "replay_link": "대화형 녹화 조사에서 근거 확인",
        "verification": "최신 검증 기록",
        "materials": "코드와 실행 자료",
        "source": "앱 소스 내려받기 (ZIP)",
        "setup": "로컬 설치·운영 안내",
        "evaluation": "평가 요약 (JSON)",
        "cases": "평가 시나리오 (JSON)",
        "license": "개인 기획 자료와 Git 이력은 소스 압축 파일에서 제외했습니다. 이 릴리스의 자체 코드에는 오픈소스 라이선스를 부여하지 않았습니다. Pretendard 폰트 라이선스를 포함했으며 모델·의존성 라이선스는 별도로 적용됩니다.",
    },
}


def build(destination, verification_directory="docs/audits/2026-09-10-final-polish"):
    from release.source_bundle import bundle

    bundle(destination / "filing-agent-source.zip")
    shutil.copyfile(ROOT / "slice/README.md", destination / "LOCAL-SETUP.md")
    audit = ROOT / verification_directory
    verification = (audit / "README.md").read_text()
    verification = verification.replace("../../adr/", "https://github.com/mhju0/filing-agent/blob/main/docs/adr/")
    verification = verification.replace("(artifact.json)", f"(https://github.com/mhju0/filing-agent/blob/main/{verification_directory}/artifact.json)")
    (destination / "VERIFICATION.md").write_text(verification)
    shutil.copyfile(audit / "verification.json", destination / "verification.json")
    shutil.copyfile(
        ROOT / "evals/release-summary.json", destination / "evaluation.json"
    )
    shutil.copyfile(ROOT / "evals/cases.json", destination / "evaluation-cases.json")
    recording = ROOT / "docs/audits/2026-09-10-final-polish"
    for name in (
        "actual-run.webm",
        "actual-run.png",
        "actual-run-en.vtt",
        "actual-run-ko.vtt",
    ):
        shutil.copyfile(recording / name, destination / name)
    css = next((destination / "assets").glob("*.css")).relative_to(destination)
    (destination / "engineering.css").write_text(
        "article.project{max-width:850px;margin:3rem auto;padding:0 1.5rem}article.project section{padding:1.5rem 0;border-bottom:1px solid var(--rule)}article.project p{max-width:72ch}article.project .lead{font-size:1.2rem}article.project .flow{border-left:3px solid var(--accent);padding:1rem;background:var(--wash)}article.project .run{margin-top:2rem;padding-top:2rem;border-top:2px solid var(--ink)}article.project video{display:block;width:100%;height:auto;background:var(--surface);border:1px solid var(--rule)}article.project .video-flow{padding-left:1.4rem}article.project li{padding:.4rem 0}article.project nav{display:flex;flex-wrap:wrap;gap:1rem}article.project h1{margin-top:2rem}article.project footer{padding:2rem 0} @media(max-width:500px){article.project{margin:1rem auto;padding:0 1rem}}"
    )
    for lang, c in COPY.items():
        e = lambda key, content=c: html.escape(content[key])
        sections = "".join(
            f"<section><h2>{e(k)}</h2><p>{e(k + '_body')}</p></section>"
            for k in (
                "story",
                "boundary",
                "state",
                "results",
                "failures",
                "limits",
                "security",
            )
        )
        sections = sections.replace(
            f"<p>{e('boundary_body')}</p>",
            f'<p>{e("boundary_body")}</p><p class="flow">{e("flow")}</p>',
        )
        sections = sections.replace(
            f"<p>{e('results_body')}</p>",
            f"<p>{e('results_body')}</p><p>{e('timing')}</p>",
        )
        sections = sections.replace(
            f"<p>{e('security_body')}</p>",
            f"<p>{e('security_body')}</p><p>{e('public_body')}</p>",
        )
        other_lang = "ko" if lang == "en" else "en"
        video_section = (
            f'<section class="run"><h2>{e("video")}</h2><p>{e("video_body")}</p>'
            f'<video controls preload="metadata" poster="actual-run.png" aria-label="{e("video")}">'
            '<source src="actual-run.webm" type="video/webm">'
            f'<track kind="captions" srclang="{lang}" label="{("English" if lang == "en" else "한국어")}" src="actual-run-{lang}.vtt" default>'
            f'<track kind="captions" srclang="{other_lang}" label="{("한국어" if other_lang == "ko" else "English")}" src="actual-run-{other_lang}.vtt">'
            f'</video><ol class="video-flow"><li>{e("video_step_one")}</li><li>{e("video_step_two")}</li></ol>'
            f'<p><a href="index.html">{e("replay_link")}</a> · '
            f'<a href="VERIFICATION.md">{e("verification")}</a></p></section>'
        )
        (destination / f"engineering-{lang}.html").write_text(
            f'''<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="favicon.png"><title>Filing Agent · {e("title")}</title><link rel="stylesheet" href="{css}"><link rel="stylesheet" href="engineering.css"><script src="theme.js"></script></head><body><main><article class="project"><nav aria-label="Language and replay"><a href="index.html">{e("back")}</a><a lang="ko" href="engineering-ko.html">한국어</a><a lang="en" href="engineering-en.html">English</a></nav><h1>{e("title")}</h1><p class="lead">{e("lead")}</p><p><a href="https://github.com/mhju0/filing-digest">Filing Digest</a> · <a href="https://mhju0.github.io/filing-digest/">{("Sister project walkthrough" if lang == "en" else "동반 프로젝트 둘러보기")}</a></p>{video_section}{sections}<section><h2>{e("materials")}</h2><ul><li><a href="filing-agent-source.zip">{e("source")}</a></li><li><a href="LOCAL-SETUP.md">{e("setup")}</a></li><li><a href="evaluation.json">{e("evaluation")}</a></li><li><a href="evaluation-cases.json">{e("cases")}</a></li></ul><p>{e("license")}</p></section><footer>Filing Agent · Michael Ju · 2026-09-11</footer></article></main></body></html>'''
        )
    csp = "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; media-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"
    config = {
        "framework": None,
        "headers": [
            {
                "source": "/(.*)",
                "headers": [
                    {"key": "Content-Security-Policy", "value": csp},
                    {"key": "X-Content-Type-Options", "value": "nosniff"},
                    {"key": "Referrer-Policy", "value": "no-referrer"},
                    {
                        "key": "Permissions-Policy",
                        "value": "camera=(), microphone=(), geolocation=()",
                    },
                ],
            }
        ],
    }
    (destination / "vercel.json").write_text(json.dumps(config, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    parser.add_argument("--verification-directory", default="docs/audits/2026-09-10-final-polish")
    args = parser.parse_args()
    build(args.destination, args.verification_directory)
