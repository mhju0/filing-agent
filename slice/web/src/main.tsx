import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import type {
  Answer,
  Figure,
  Investigation,
  Lang,
  Replay,
  Turn,
} from "./types";
import "./styles.css";
import glossary from "./glossary.json";

const replayMode = document.documentElement.dataset.mode === "replay";
const replayLocation = new URLSearchParams(location.hash.slice(1));
const boundedIndex = (key: string) => Math.max(0, Math.min(2, Number(replayLocation.get(key)) || 0));
let token = "";
async function api(path: string, body?: unknown) {
  const r = await fetch("/api" + path, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined
        ? {}
        : { "Content-Type": "application/json", "X-Filing-Token": token },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok) throw new Error(data.detail || "Local request failed");
  return data;
}
const metricNames: Record<string, string[]> = glossary.metrics;
const companyNames: Record<string, string[]> = glossary.companies;
function readDraft(id: string | null) {
  try {
    const d = JSON.parse(
      localStorage.getItem("filing-draft-" + (id || "new")) || "null",
    );
    return d && Date.now() - d.at < 30 * 86400000 ? d.text : "";
  } catch {
    return "";
  }
}
function label(map: Record<string, string[]>, key: string, lang: Lang) {
  return map[key]?.[lang === "ko" ? 0 : 1] || key;
}
function exact(value: string) {
  const [a, b] = value.split(".");
  return BigInt(a).toLocaleString("en-US") + (b ? "." + b : "");
}
function compact(f: Figure, lang: Lang) {
  const divisor = f.currency === "KRW" ? 1000000000000n : 1000000000n;
  const v = BigInt(f.value);
  const sign = v < 0n ? "−" : "";
  const tenths = ((v < 0n ? -v : v) * 10n + divisor / 2n) / divisor;
  return (
    (((v < 0n ? -v : v) * 10n) % divisor === 0n ? "" : "≈ ") +
    sign +
    (tenths / 10n).toLocaleString("en-US") +
    "." +
    (tenths % 10n) +
    (f.currency === "KRW" ? (lang === "ko" ? "조원" : "tn KRW") : "bn USD")
  );
}
const busy = (t: Turn) => ["running", "queued"].includes(t.status);

function Modal({
  children,
  close,
  title,
}: {
  children: React.ReactNode;
  close: () => void;
  title: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement;
    ref.current?.showModal();
    return () => {
      if (opener?.isConnected) opener.focus();
    };
  }, []);
  return (
    <dialog
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        close();
      }}
      onKeyDown={(e) => {
        if (e.key !== "Tab") return;
        const controls = Array.from(e.currentTarget.querySelectorAll<HTMLElement>(
          'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex="0"]',
        )).filter((el) => el.getClientRects().length > 0);
        const first = controls[0];
        const last = controls[controls.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }}
      aria-label={title}
    >
      <div className="panel-head">
        <h2>{title}</h2>
        <button onClick={close}>
          {/[가-힣]/.test(title) ? "닫기" : "Close"}
        </button>
      </div>
      {children}
    </dialog>
  );
}

function App() {
  const [lang, setLang] = useState<Lang>(
    localStorage.getItem("filing-language") === "en" ? "en" : "ko",
  );
  const [theme, setTheme] = useState(
    localStorage.getItem("filing-theme") || "system",
  );
  const [systemDark, setSystemDark] = useState(
    matchMedia("(prefers-color-scheme: dark)").matches,
  );
  const [narrow, setNarrow] = useState(
    matchMedia("(max-width: 850px)").matches,
  );
  const [current, setCurrent] = useState<Investigation | null>(null);
  const [history, setHistory] = useState<Investigation[] | null>(null);
  const [draft, setDraft] = useState(() =>
    replayMode ? "" : readDraft(localStorage.getItem("filing-investigation")),
  );
  const [error, setError] = useState("");
  const [evidence, setEvidence] = useState<Figure | Answer | null>(null);
  const [replay, setReplay] = useState<Replay | null>(null);
  const [scenario, setScenario] = useState(replayMode ? boundedIndex("scenario") : 0);
  const [turnIndex, setTurnIndex] = useState(replayMode ? boundedIndex("turn") : 0);
  const [ready, setReady] = useState(false);
  const [sending, setSending] = useState(false);
  const [clock, setClock] = useState(Date.now());
  const [deleteTarget, setDeleteTarget] = useState<Investigation | null>(null);
  const [historyQuery, setHistoryQuery] = useState("");
  const prompt = useRef<HTMLTextAreaElement>(null);
  const selectedRef = useRef<HTMLElement | null>(null);
  const autoSeen = useRef("");
  const t = (ko: string, en: string) => (lang === "ko" ? ko : en);
  const dark = theme === "system" ? systemDark : theme === "dark";
  const active = current?.turns.some(busy) || false;
  useEffect(() => {
    if (!active) return;
    const timer = setInterval(() => setClock(Date.now()), 250);
    return () => clearInterval(timer);
  }, [active]);
  useEffect(() => {
    const media = matchMedia("(prefers-color-scheme: dark)");
    const change = () => setSystemDark(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    const media = matchMedia("(max-width: 850px)");
    const change = () => setNarrow(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);
  useEffect(() => {
    document.documentElement.lang = lang;
    localStorage.setItem("filing-language", lang);
  }, [lang]);
  useEffect(() => {
    if (replayMode) {
      fetch("./recording.json")
        .then((r) => {
          if (!r.ok) throw new Error("Recorded asset unavailable");
          return r.json();
        })
        .then((d) => {
          if (
            !Array.isArray(d.investigations) ||
            !d.investigations.length ||
            d.investigations.some(
              (i: Investigation) => !Array.isArray(i.turns) || !i.turns.length,
            )
          )
            throw new Error("Invalid recording");
          const selected = Math.min(boundedIndex("scenario"), d.investigations.length - 1);
          setScenario(selected);
          setTurnIndex(Math.min(boundedIndex("turn"), d.investigations[selected].turns.length - 1));
          setReplay(d);
          setReady(true);
        })
        .catch((e) => setError(e.message));
    } else {
      api("/session")
        .then(async (d) => {
          token = d.token;
          setReady(true);
          const id = localStorage.getItem("filing-investigation");
          if (id) {
            try {
              setCurrent(await api("/investigations/" + id));
            } catch {
              localStorage.removeItem("filing-investigation");
            }
          }
        })
        .catch((e) => setError(e.message));
    }
  }, []);
  useEffect(() => {
    if (!replayMode && current)
      localStorage.setItem("filing-investigation", current.id);
  }, [current?.id]);
  useEffect(() => {
    if (!replayMode && ready) {
      localStorage.setItem(
        "filing-draft-" + (current?.id || "new"),
        JSON.stringify({ text: draft, at: Date.now() }),
      );
      for (const key of Object.keys(localStorage)) {
        if (
          key.startsWith("filing-draft-") &&
          !readDraft(key.slice("filing-draft-".length))
        )
          localStorage.removeItem(key);
      }
    }
  }, [draft, current?.id, ready]);
  useEffect(() => {
    if (!current || !active || replayMode) return;
    const timer = setInterval(
      () =>
        api("/investigations/" + current.id)
          .then(setCurrent)
          .catch((e) => setError(e.message)),
      350,
    );
    return () => clearInterval(timer);
  }, [current?.id, active]);
  useEffect(() => {
    if (!replay) return;
    const inv = replay.investigations[scenario];
    window.history.replaceState(null, "", `#scenario=${scenario}&turn=${turnIndex}`);
    setCurrent(inv);
    const turn = inv.turns[turnIndex];
    setEvidence(
      !narrow && turnIndex === 0
        ? turn?.answer?.figures[0] || turn?.answer || null
        : null,
    );
  }, [replay, scenario, turnIndex, narrow]);
  useEffect(() => {
    if (replayMode || !current) return;
    const last = current.turns.at(-1);
    if (
      last?.status === "complete" &&
      last.answer?.reason_code &&
      last.answer.operation !== "clarify" &&
      autoSeen.current !== last.id
    ) {
      autoSeen.current = last.id;
      setEvidence(last.answer);
    }
    if (
      last &&
      [
        "error",
        "cancelled",
        "timeout",
        "interrupted",
        "stop_unconfirmed",
      ].includes(last.status) &&
      autoSeen.current !== last.id
    ) {
      autoSeen.current = last.id;
      setDraft(last.question);
    }
  }, [current]);
  async function action(fn: () => Promise<void>) {
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    }
  }
  async function newInvestigation(text = "") {
    setSending(true);
    try {
      const inv = await api("/investigations", {});
      setCurrent(inv);
      setEvidence(null);
      setDraft(text);
    } finally {setSending(false);}
    requestAnimationFrame(()=>prompt.current?.focus());
  }
  async function submit(question = draft, retry?: Turn) {
    if (!question.trim() || sending || active) return;
    setSending(true);
    await action(async () => {
      const inv = current || (await api("/investigations", {}));
      const turn = await api("/investigations/" + inv.id + "/turns", {
        question,
        language: retry?.language || lang,
        request_id: crypto.randomUUID(),
        retry_of: retry?.id,
      });
      setCurrent({ ...inv, turns: [...inv.turns, turn] });
      setDraft("");
    });
    setSending(false);
  }
  function inspect(value: Figure | Answer, e?: React.MouseEvent<HTMLElement>) {
    selectedRef.current = e?.currentTarget || null;
    setEvidence(value);
  }
  function closeEvidence() {
    setEvidence(null);
    selectedRef.current?.focus();
  }
  const turns = current
    ? replayMode
      ? current.turns.slice(0, turnIndex + 1)
      : current.turns
    : [];
  const selected = "id" in (evidence || {}) ? (evidence as Figure).id : null;
  const context = current?.pending || current?.accepted;
  const sourceView =
    evidence &&
    ("id" in evidence ? (
      <>
        <p className="eyebrow">
          {t("원문 발췌 · 번역 아님", "Original excerpt · not translated")}
        </p>
        <div
          className="excerpt"
          lang={evidence.source.regulator === "dart" ? "ko" : "en"}
        >
          <strong>{evidence.source_label}</strong>
          <p>
            <mark>{evidence.original_value}</mark> ({evidence.original_unit})
          </p>
          <p className="muted">
            {evidence.source.excerpt ||
              evidence.source.excerpt_cells?.join(" · ")}
          </p>
        </div>
        <p>
          {label(companyNames, evidence.company, lang)} ·{" "}
          {evidence.source.filing_title} · FY{evidence.period}
        </p>
        <p className="muted">
          {evidence.source.section || "Inline XBRL"} ·{" "}
          {t("연결", "Consolidated")} · {evidence.period_start} ~{" "}
          {evidence.period_end}
        </p>
        <p className="reconcile">
          {t("원문", "Source")}: {evidence.original_value} (
          {evidence.original_unit}) → {t("표시", "Display")}:{" "}
          {compact(evidence, lang)}
        </p>
        <p className="muted">
          {t("정확한 값", "Exact value")}: {exact(evidence.value)}{" "}
          {evidence.currency}
        </p>
        <a
          className="source-link"
          href={evidence.source.url}
          target="_blank"
          rel="noreferrer"
        >
          {t("원문 열기", "Open original filing")} ↗
        </a>
        {evidence.source.regulator === "sec" && (
          <p className="limitation">
            {t(
              "SEC는 자동화된 접근을 제한할 수 있습니다. 공시 링크는 새 탭에서 열립니다.",
              "SEC may restrict automated access. The filing link opens in a new tab.",
            )}
          </p>
        )}
        <p className="muted">
          {t(
            "고정된 과거 공시입니다. 이후 정정 공시 전체를 검토한 결과는 아닙니다.",
            "Pinned historical filing; later amendments have not been exhaustively reviewed.",
          )}
        </p>
      </>
    ) : (
      <>
        <h3>{t("검증된 자료에서 확인한 범위", "Verified catalog checked")}</h3>
        <p>{evidence[lang === "ko" ? "answer_ko" : "answer_en"]}</p>
        <p className="limitation">
          {t(
            "검증된 지표 목록을 조회했습니다. 공시 전체를 검색했다는 뜻은 아닙니다.",
            "This lookup checked the verified metric catalog, not the full filings.",
          )}
        </p>
        <ul className="trail">
          {evidence.searched.map((s, i) => (
            <li key={i}>
              {s.company} · {s.filing_title}
              <br />
              {s.section}
            </li>
          ))}
        </ul>
      </>
    ));

  return (
    <>
      <a className="skip" href="#conversation">
        {t("대화로 이동", "Skip to conversation")}
      </a>
      <div className="sr-only" aria-live="polite">
        {active
          ? t("질문을 처리하고 있습니다.", "Processing the question.")
          : current?.turns.at(-1)?.status === "complete"
            ? t("답변이 준비되었습니다.", "The answer is ready.")
            : ""}
      </div>
      <header>
        <a className="wordmark" href={replayMode ? "./index.html" : "/"}>
          Filing Agent
        </a>
        <nav aria-label={t("조사 탐색", "Investigation navigation")}>
          {!replayMode && (
            <>
              <button
                onClick={() => action(() => newInvestigation())}
                disabled={active || sending || !ready}
              >
                {t("새 조사", "New investigation")}
              </button>
              <button
                onClick={() =>
                  action(async () => setHistory(await api("/history")))
                }
              >
                {t("기록", "History")}
              </button>
            </>
          )}
          {replayMode && <a className="project-link" href={lang === "ko" ? "./engineering-ko.html" : "./engineering-en.html"}>{t("프로젝트 소개", "About the project")}</a>}
          <div className="languages" aria-label="Language">
            <button
              lang="ko"
              aria-pressed={lang === "ko"}
              onClick={() => setLang("ko")}
            >
              한국어
            </button>
            <button
              lang="en"
              aria-pressed={lang === "en"}
              onClick={() => setLang("en")}
            >
              English
            </button>
          </div>
          <button
            className="theme"
            aria-label={
              dark
                ? t("밝은 테마로 전환", "Switch to light theme")
                : t("어두운 테마로 전환", "Switch to dark theme")
            }
            onClick={() => {
              const v = dark ? "light" : "dark";
              setTheme(v);
              localStorage.setItem("filing-theme", v);
            }}
          >
            {dark ? "☀" : "☾"}
          </button>
        </nav>
      </header>
      <div className="mode-line">
        {replayMode
          ? t(
              "녹화된 조사 · 질문을 입력할 수 없습니다",
              "Recorded investigation · no live questions",
            )
          : t(
              "로컬 조사 · 검증된 과거 공시",
              "Local investigation · verified historical filings",
            )}
      </div>
      {replayMode && replay && (
        <nav
          className="replay-nav"
          aria-label={t("녹화 탐색", "Replay navigation")}
        >
          <label>
            {t("조사", "Investigation")}{" "}
            <select
              value={scenario}
              onChange={(e) => {
                setScenario(Number(e.target.value));
                setTurnIndex(0);
              }}
            >
              {replay.investigations.map((_, i) => (
                <option key={i} value={i}>
                  {[
                    t("연간 비교", "Annual comparison"),
                    t("회사 전환", "Company switch"),
                    t("근거 부족", "Insufficient evidence"),
                  ][i] || i + 1}
                </option>
              ))}
            </select>
          </label>
          <button
            disabled={turnIndex === 0}
            onClick={() => setTurnIndex(turnIndex - 1)}
          >
            {t("이전 질문", "Previous turn")}
          </button>
          <span>
            {turnIndex + 1} / {current?.turns.length || 1}
          </span>
          <button
            disabled={turnIndex >= (current?.turns.length || 1) - 1}
            onClick={() => setTurnIndex(turnIndex + 1)}
          >
            {t("다음 질문", "Next turn")}
          </button>
        </nav>
      )}
      <main
        className={
          evidence && !narrow ? "workspace with-evidence" : "workspace"
        }
      >
        <section
          className="conversation"
          id="conversation"
          aria-label={t("조사 대화", "Investigation conversation")}
        >
          {turns.length === 0 && replayMode ? (
            <div className="start">
              <h1>{t("녹화된 공시 조사", "Recorded filing investigations")}</h1>
              <p role="status">
                {error
                  ? t(
                      "녹화 자료를 불러오지 못했습니다.",
                      "The recording could not be loaded.",
                    )
                  : t(
                      "녹화 자료를 불러오는 중입니다.",
                      "Loading the recording.",
                    )}
              </p>
              {error && (
                <button onClick={() => location.reload()}>
                  {t("다시 불러오기", "Reload recording")}
                </button>
              )}
            </div>
          ) : turns.length === 0 ? (
            <div className="start">
              <p className="eyebrow">
                {t(
                  "공시를 읽는 또 하나의 방법",
                  "Read filings through questions",
                )}
              </p>
              <h1>{t("수치에서 근거까지.", "From figures to evidence.")}</h1>
              <p>
                {t(
                  "회사와 회계연도를 정하고, 다음 질문을 이어가세요.",
                  "Choose a company and fiscal year, then follow the evidence.",
                )}
              </p>
              <table className="coverage">
                <caption>
                  {t(
                    "검증된 범위 · 연결 매출액, 영업이익, 당기순이익",
                    "Verified coverage · consolidated revenue, operating income, net income",
                  )}
                </caption>
                <thead>
                  <tr>
                    <th>{t("회사", "Company")}</th>
                    <th>2022</th>
                    <th>2023</th>
                    <th>2024</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    ["Samsung", "✓", "✓", "—"],
                    ["NAVER", "—", "✓", "—"],
                    ["Microsoft", "—", "✓", "✓"],
                  ].map((row) => (
                    <tr key={row[0]}>
                      <th>{label(companyNames, row[0], lang)}</th>
                      {row.slice(1).map((v, i) => (
                        <td key={i}>{v}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="examples">
                {[
                  "삼성전자 2023년과 2022년 매출액 증감률은?",
                  "네이버 2023년 영업이익은?",
                  "Compare Microsoft revenue in FY2024 and FY2023.",
                  "삼성전자 2023년 연구개발비는?",
                ].map((q) => (
                  <button
                    key={q}
                    onClick={() => {
                      setDraft(q);
                      prompt.current?.focus();
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              <div className="investigation-heading">
                <h1>
                  {replayMode
                    ? [
                        t(
                          "삼성전자 연간 매출 비교",
                          "Samsung annual revenue comparison",
                        ),
                        t(
                          "질문을 이어 회사 바꾸기",
                          "Switching companies in conversation",
                        ),
                        t(
                          "검증된 근거가 없을 때",
                          "When verified evidence is missing",
                        ),
                      ][scenario]
                    : t("공시 조사", "Filing investigation")}
                </h1>
                {current?.saved && (
                  <span>
                    {t("저장됨 · 원본 보존", "Saved · original preserved")}
                  </span>
                )}
              </div>
              {!replayMode && current?.lineage && (
                <p className="muted">
                  {current.lineage.mode === "continue"
                    ? t(
                        "저장본에서 이어진 새 조사 · 원본 근거 유지",
                        "New investigation continued from saved results · original evidence",
                      )
                    : t(
                        "새 조사 · 현재 검증 자료 사용",
                        "New investigation · current verified evidence",
                      )}
                </p>
              )}
              {turns.map((turn) => (
                <article className="turn" key={turn.id} data-turn={turn.id}>
                  <div className="question">
                    <div>
                      <h2>
                        {replayMode && lang === "en" && turn.question_en
                          ? turn.question_en
                          : turn.question}
                      </h2>
                      {replayMode && lang === "en" && turn.question_en && (
                        <details>
                          <summary>
                            Translated question · original Korean
                          </summary>
                          <p lang="ko">{turn.question}</p>
                        </details>
                      )}
                    </div>
                    {!replayMode && (
                      <button
                        disabled={active}
                        onClick={() =>
                          action(() => newInvestigation(turn.question))
                        }
                      >
                        {t("새 조사로 편집", "Edit as new")}
                      </button>
                    )}
                  </div>
                  {turn.answer && (
                    <div
                      className="answer"
                      lang={replayMode ? lang : turn.language}
                    >
                      <div className="figures">
                        {turn.answer.figures.length ? (
                          turn.answer.figures.map((f) => (
                            <button
                              key={f.id}
                              className={
                                "figure " +
                                (selected === f.id ? "selected" : "")
                              }
                              onClick={(e) => inspect(f, e)}
                              aria-label={`${label(companyNames, f.company, lang)} FY${f.period} ${label(metricNames, f.metric, lang)} ${compact(f, replayMode ? lang : turn.language)} ${t("근거", "source")}`}
                            >
                              <span>
                                {label(
                                  companyNames,
                                  f.company,
                                  replayMode ? lang : turn.language,
                                )}{" "}
                                · FY{f.period}
                              </span>
                              <strong>
                                {compact(f, replayMode ? lang : turn.language)}
                              </strong>
                              <small>
                                {label(
                                  metricNames,
                                  f.metric,
                                  replayMode ? lang : turn.language,
                                )}{" "}
                                · {f.source.regulator.toUpperCase()}
                              </small>
                            </button>
                          ))
                        ) : (
                          <div className="missing">
                            <strong>—</strong>
                            <span>
                              {t("검증된 수치 없음", "No verified figure")}
                            </span>
                          </div>
                        )}
                      </div>
                      <p className="answer-sentence">
                        {
                          turn.answer[
                            (replayMode ? lang : turn.language) === "ko"
                              ? "answer_ko"
                              : "answer_en"
                          ]
                        }
                      </p>
                      {turn.answer.figures.length > 0 && (
                        <table className="answer-table">
                          <caption>
                            {label(
                              metricNames,
                              turn.answer.figures[0].metric,
                              replayMode ? lang : turn.language,
                            )}
                          </caption>
                          <thead>
                            <tr>
                              <th>{t("회계연도", "Fiscal year")}</th>
                              <th>{t("공시 수치", "Reported value")}</th>
                              <th>{t("근거", "Source")}</th>
                            </tr>
                          </thead>
                          <tbody>
                            {turn.answer.figures.map((f) => (
                              <tr key={f.id}>
                                <th scope="row">{f.period}</th>
                                <td>
                                  {compact(
                                    f,
                                    replayMode ? lang : turn.language,
                                  )}
                                </td>
                                <td>
                                  <button
                                    className="figure-source"
                                    aria-label={`FY${f.period} ${f.source.regulator.toUpperCase()} ${t("근거 보기", "Inspect source")}`}
                                    onClick={(e) => inspect(f, e)}
                                  >
                                    {f.source.regulator.toUpperCase()}
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                      {turn.answer.calculated.map((c, i) => (
                        <details className="formula" key={i}>
                          <summary>
                            {t("계산됨", "calc")} · {c.percentage_change}%
                          </summary>
                          <p>(current − prior) ÷ prior × 100</p>
                          <p>
                            {t("차이", "Absolute change")}:{" "}
                            {exact(c.absolute_change)} {c.currency}
                          </p>
                          {c.inputs.map((id) => {
                            const f = turn.answer!.figures.find(
                              (f) => f.id === id,
                            )!;
                            return (
                              <button key={id} onClick={(e) => inspect(f, e)}>
                                FY{f.period} · {exact(f.value)} {f.currency} ·{" "}
                                {f.source.regulator.toUpperCase()}
                              </button>
                            );
                          })}
                        </details>
                      ))}
                      {turn.answer.reason_code &&
                        turn.answer.operation !== "clarify" && (
                          <button onClick={(e) => inspect(turn.answer!, e)}>
                            {t(
                              "확인한 근거 범위",
                              "Inspect checked evidence scope",
                            )}
                          </button>
                        )}
                      {turn.answer.operation === "clarify" &&
                        !replayMode &&
                        turn.id === current?.turns.at(-1)?.id && (
                          <div className="choices">
                            {(!turn.intent?.companies.length
                              ? ["삼성전자", "네이버", "Microsoft"]
                              : !turn.intent?.periods.length
                                ? ["2022", "2023", "2024"]
                                : ["매출액", "영업이익", "당기순이익"]
                            ).map((choice) => (
                              <button
                                disabled={active || current?.saved}
                                key={choice}
                                onClick={() => submit(choice)}
                              >
                                {choice}
                              </button>
                            ))}
                          </div>
                        )}
                    </div>
                  )}
                  {turn.error && (
                    <p className="error" role="status">
                      {t(
                        "로컬 실행이 완료되지 않았습니다.",
                        "Local execution did not complete.",
                      )}{" "}
                      {turn.error}
                    </p>
                  )}
                  <details className="steps" open={busy(turn)}>
                    <summary>
                      {busy(turn)
                        ? t("실행 중", "Running")
                        : t("실행 기록", "Execution record")}{" "}
                      ·{" "}
                      {turn.wall_seconds?.toFixed(2) ||
                        (busy(turn)
                          ? Math.max(
                              0,
                              (clock - Date.parse(turn.created_at)) / 1000,
                            ).toFixed(1)
                          : "…")}
                      s {replayMode ? "actual · recorded" : ""}
                    </summary>
                    <ol>
                      {turn.steps.map((s) => (
                        <li key={s.name}>
                          <span>
                            {
                              (
                                {
                                  interpret: t(
                                    "질문 해석",
                                    "Interpret question",
                                  ),
                                  evidence: t(
                                    "검증 자료 조회 및 계산",
                                    "Resolve evidence and calculate",
                                  ),
                                  answer: t("답변 저장", "Persist answer"),
                                } as Record<string, string>
                              )[s.name]
                            }
                          </span>{" "}
                          ·{" "}
                          {(
                            {
                              complete: t("완료", "Complete"),
                              running: t("실행 중", "Running"),
                              pending: t("대기", "Pending"),
                              interrupted: t("중단됨", "Interrupted"),
                              cancelled: t("취소됨", "Cancelled"),
                              error: t("실패", "Failed"),
                              timeout: t("시간 초과", "Timed out"),
                              stop_unconfirmed: t(
                                "중지 미확인",
                                "Stop unconfirmed",
                              ),
                            } as Record<string, string>
                          )[s.status] || s.status}{" "}
                          {s.seconds !== undefined
                            ? `${s.seconds.toFixed(2)}s`
                            : s.status === "running" && s.started_at
                              ? `${Math.max(0, (clock - Date.parse(s.started_at)) / 1000).toFixed(1)}s`
                              : ""}{" "}
                          {s.reused
                            ? t("(완료 단계 재사용)", "(completed step reused)")
                            : ""}
                        </li>
                      ))}
                    </ol>
                  </details>
                  {!replayMode &&
                    busy(turn) &&
                    clock - Date.parse(turn.created_at) > 2000 && (
                      <button
                        onClick={() =>
                          action(async () => {
                            await api("/turns/" + turn.id + "/cancel", {});
                          })
                        }
                      >
                        {t("취소", "Cancel")}
                      </button>
                    )}
                  {!replayMode &&
                    [
                      "error",
                      "cancelled",
                      "timeout",
                      "interrupted",
                      "stop_unconfirmed",
                    ].includes(turn.status) &&
                    !turn.retry_of &&
                    !current?.turns.some((t) => t.retry_of === turn.id) && (
                      <button
                        disabled={active || current?.saved}
                        onClick={() => submit(turn.question, turn)}
                      >
                        {t("한 번 다시 시도", "Retry once")}
                      </button>
                    )}
                </article>
              ))}
            </>
          )}
          {!replayMode && (
            <div className="composer">
              {current && turns.length > 0 && !active && (
                <div className="actions">
                  {!current.saved && (
                    <button
                      onClick={() =>
                        action(async () =>
                          setCurrent(
                            await api(
                              "/investigations/" + current.id + "/save",
                              {},
                            ),
                          ),
                        )
                      }
                    >
                      {t("조사 저장", "Save investigation")}
                    </button>
                  )}
                  {current.saved &&
                    ["continue", "refresh"].map((mode) => (
                      <button
                        key={mode}
                        onClick={() =>
                          action(async () => {
                            const next = await api(
                              "/investigations/" + current.id + "/fork",
                              { mode },
                            );
                            setCurrent(next);
                            setEvidence(null);
                            setDraft(
                              mode === "refresh"
                                ? current.turns.at(-1)?.question || ""
                                : "",
                            );
                          })
                        }
                      >
                        {mode === "continue"
                          ? t(
                              "원본 근거로 계속",
                              "Continue with original evidence",
                            )
                          : t(
                              "최신 검증 자료로 새 조사",
                              "Refresh into new investigation",
                            )}
                      </button>
                    ))}
                </div>
              )}
              {context && (
                <div className="context">
                  {current?.pending
                    ? t("확인 중인 문맥", "Pending clarification")
                    : t("확정된 문맥", "Accepted context")}
                  :{" "}
                  {context.companies.map((c) => (
                    <span className="context-chip" key={c}>
                      {label(companyNames, c, lang)}
                    </span>
                  ))}
                  <span className="context-chip">
                    {context.metric
                      ? label(metricNames, context.metric, lang)
                      : "—"}
                  </span>
                  {context.periods.map((p) => (
                    <span className="context-chip" key={p}>
                      {p}
                    </span>
                  ))}
                </div>
              )}
              {error && (
                <p className="error" role="alert">
                  {error}
                </p>
              )}
              {!current?.saved && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    void submit();
                  }}
                >
                  <label htmlFor="prompt">
                    {t("공시에 대해 질문하기", "Ask about a filing")}
                  </label>
                  <div className="prompt-row">
                    <textarea
                      id="prompt"
                      disabled={sending}
                      ref={prompt}
                      rows={2}
                      maxLength={2000}
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (
                          e.key === "Enter" &&
                          !e.shiftKey &&
                          !e.nativeEvent.isComposing
                        ) {
                          e.preventDefault();
                          void submit();
                        }
                      }}
                      placeholder={t(
                        "회사, 지표, 회계연도를 입력하세요",
                        "Company, metric, fiscal year",
                      )}
                    />
                    <button
                      className="send"
                      disabled={!ready || sending || active || !draft.trim()}
                      type="submit"
                    >
                      {t("질문", "Ask")}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
          {replayMode && error && <p role="alert">{error}</p>}
        </section>
        {evidence && !narrow && (
          <aside className="evidence" aria-label={t("근거", "Evidence")}>
            <div className="panel-head">
              <h2>{t("근거", "Evidence")}</h2>
              <button onClick={closeEvidence}>{t("닫기", "Close")}</button>
            </div>
            {sourceView}
          </aside>
        )}
      </main>
      {evidence && narrow && (
        <Modal title={t("근거", "Evidence")} close={closeEvidence}>
          {sourceView}
        </Modal>
      )}
      {history && (
        <Modal title={t("기록", "History")} close={() => setHistory(null)}>
          <label>
            {t("기록 검색", "Search history")}
            <input
              type="search"
              value={historyQuery}
              onChange={(e) => setHistoryQuery(e.target.value)}
            />
          </label>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          <p className="muted">
            {t(
              "일반 조사는 30일간 활동이 없으면 만료됩니다. 저장된 조사는 삭제할 때까지 보존됩니다.",
              "Ordinary investigations expire after 30 idle days. Saved investigations remain until deleted.",
            )}
          </p>
          {history.length > 0 && historyQuery && !history.some((inv) => inv.turns.some((turn) => turn.question.toLowerCase().includes(historyQuery.toLowerCase()))) && <p>{t("일치하는 조사가 없습니다.", "No matching investigations.")}</p>}
          {history.length === 0 ? (
            <p>{t("아직 조사가 없습니다.", "No investigations yet.")}</p>
          ) : (
            history
              .filter(
                (inv) =>
                  inv.turns.some((turn) =>
                    turn.question
                      .toLowerCase()
                      .includes(historyQuery.toLowerCase()),
                  ) || !historyQuery,
              )
              .map((inv) => (
                <div className="history-item" key={inv.id}>
                  <button
                    className="history-row"
                    onClick={() => {
                      setCurrent(inv);
                      setHistory(null);
                      setEvidence(null);
                      setDraft(readDraft(inv.id));
                    }}
                  >
                    {inv.turns[0]?.question ||
                      t("새 조사", "New investigation")}
                    <small>
                      {inv.saved ? t("저장됨", "Saved") : t("최근", "Recent")} ·{" "}
                      {new Date(inv.created_at).toLocaleDateString(lang)}
                    </small>
                  </button>
                  <button
                    aria-label={t("이 조사 삭제", "Delete this investigation")}
                    disabled={inv.turns.some(busy)}
                    onClick={() => setDeleteTarget(inv)}
                  >
                    {t("삭제", "Delete")}
                  </button>
                </div>
              ))
          )}
        </Modal>
      )}
      {deleteTarget && (
        <Modal
          title={t("조사 삭제", "Delete investigation")}
          close={() => setDeleteTarget(null)}
        >
          <p>
            {t(
              "질문과 저장된 답변이 이 Mac에서 삭제됩니다. 별도로 만든 백업에는 남을 수 있습니다.",
              "Questions and saved answers will be deleted from this Mac. Separate backups may still contain them.",
            )}
          </p>
          <button
            onClick={() =>
              action(async () => {
                await api("/investigations/" + deleteTarget.id + "/delete", {});
                localStorage.removeItem("filing-draft-" + deleteTarget.id);
                if (current?.id === deleteTarget.id) {
                  setDraft("");
                  setCurrent(null);
                  setEvidence(null);
                  localStorage.removeItem("filing-investigation");
                }
                setHistory(await api("/history"));
                setDeleteTarget(null);
              })
            }
          >
            {t("삭제 확인", "Confirm deletion")}
          </button>
        </Modal>
      )}
    </>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
