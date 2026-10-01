import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  AnimatePresence,
  MotionConfig,
  motion,
  useIsPresent,
  useReducedMotion,
} from "motion/react";
import type {
  Answer,
  Figure,
  Investigation,
  Lang,
  Turn,
} from "./types";
import "./styles.css";
import { useLiveInvestigation, executing, unresolved } from "./live";
import { useReplayInvestigation } from "./replay";
import { compact, exact, signedPercent } from "./format";
import { pick, scenarios, type Destination, type View } from "./content";
import { EvidenceBody, Guide, Home, Ledger, SourceBadge, label, periodLabel, useLedger } from "./views";

const replayMode = document.documentElement.dataset.mode === "replay";
const busy = executing;

function initialView(): View {
  const hash = location.hash.slice(1);
  if (hash.startsWith("guide")) return "guide";
  if (hash.startsWith("ledger")) return "ledger";
  if (hash.includes("scenario=")) return "investigate";
  return replayMode ? "home" : "investigate";
}

type SurfaceOrigin = { x: number; y: number } | null;
const surfaceSpring = {
  type: "spring",
  stiffness: 520,
  damping: 42,
  mass: 0.9,
} as const;

function originOf(element?: HTMLElement | null): SurfaceOrigin {
  if (!element) return null;
  const rect = element.getBoundingClientRect();
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

function modalOffset(origin: SurfaceOrigin) {
  if (!origin) return { x: 0, y: 28 };
  return {
    x: Math.max(-72, Math.min(72, origin.x - window.innerWidth / 2)),
    y: Math.max(-72, Math.min(72, origin.y - window.innerHeight / 2)),
  };
}

function Modal({
  active = true,
  children,
  close,
  evidenceSurface = false,
  origin,
  title,
}: {
  active?: boolean;
  children: React.ReactNode;
  close: () => void;
  evidenceSurface?: boolean;
  origin?: SurfaceOrigin;
  title: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const opener = useRef<HTMLElement | null>(null);
  const present = useIsPresent();
  const reduceMotion = useReducedMotion();
  const offset = modalOffset(origin || null);
  useEffect(() => {
    opener.current = document.activeElement as HTMLElement;
  }, []);
  useEffect(() => {
    if (!present || !active) return;
    let cancelled = false;
    queueMicrotask(() => {
      if (cancelled || ref.current?.contains(document.activeElement)) return;
      ref.current?.querySelector<HTMLElement>("button")?.focus({ preventScroll: true });
    });
    return () => { cancelled = true; };
  }, [present, active]);
  useEffect(() => {
    if (!present && ref.current?.contains(document.activeElement) && opener.current?.isConnected) {
      opener.current.focus({ preventScroll: true });
    }
  }, [present]);
  useEffect(() => {
    if (!present || !active) return;
    const previous = document.documentElement.style.overflow;
    document.documentElement.style.overflow = "hidden";
    return () => { document.documentElement.style.overflow = previous; };
  }, [present, active]);
  return (
    <motion.div
      className="modal-layer"
      data-exiting={!present || undefined}
      inert={!present || !active || undefined}
      aria-hidden={!present || !active || undefined}
      initial={{ backgroundColor: reduceMotion ? "rgba(17, 17, 17, 0.48)" : "rgba(17, 17, 17, 0)" }}
      animate={{ backgroundColor: "rgba(17, 17, 17, 0.48)" }}
      exit={{ backgroundColor: "rgba(17, 17, 17, 0)" }}
      transition={reduceMotion ? { duration: 0.01 } : surfaceSpring}
    >
      <motion.div
        ref={ref}
        className={evidenceSurface ? "modal-surface evidence-modal" : "modal-surface"}
        role={present && active ? "dialog" : undefined}
        aria-modal={present && active || undefined}
        aria-label={title}
        initial={reduceMotion ? { opacity: 1 } : { opacity: 0.72, scale: 0.96, ...offset }}
        animate={{ opacity: 1, scale: 1, x: 0, y: 0 }}
        exit={reduceMotion ? { opacity: 0 } : { opacity: 0.72, scale: 0.96, ...offset }}
        transition={reduceMotion ? { duration: 0.01 } : surfaceSpring}
        onKeyDown={(e) => {
          if (!active) return;
          if (e.key === "Escape") {
            e.preventDefault();
            close();
            return;
          }
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
      >
        <div className="panel-head">
          <h2>{title}</h2>
          <button onClick={close}>
            {/[가-힣]/.test(title) ? "닫기" : "Close"}
          </button>
        </div>
        {children}
      </motion.div>
    </motion.div>
  );
}

function DesktopEvidence({
  children,
  close,
  origin,
  reduceMotion,
  title,
}: {
  children: React.ReactNode;
  close: () => void;
  origin: SurfaceOrigin;
  reduceMotion: boolean | null;
  title: string;
}) {
  const present = useIsPresent();
  const offsetY = origin
    ? Math.max(-36, Math.min(36, origin.y - innerHeight / 2))
    : 0;
  return (
    <motion.aside
      className="evidence"
      aria-label={present ? title : undefined}
      aria-hidden={!present || undefined}
      inert={!present || undefined}
      initial={reduceMotion ? { opacity: 0 } : { opacity: 0.74, x: -24, y: offsetY }}
      animate={{ opacity: 1, x: 0, y: 0 }}
      exit={reduceMotion ? { opacity: 0 } : { opacity: 0.74, x: -24, y: offsetY }}
      transition={reduceMotion ? { duration: 0.01 } : surfaceSpring}
    >
      <div className="panel-head">
        <h2>{title}</h2>
        <button onClick={close}>{/[가-힣]/.test(title) ? "닫기" : "Close"}</button>
      </div>
      {children}
    </motion.aside>
  );
}


type Session = ReturnType<typeof useLiveInvestigation> | ReturnType<typeof useReplayInvestigation>;
function LiveApp() {
  const [view, setView] = useState<View>(initialView);
  return <Workspace session={useLiveInvestigation()} view={view} setView={setView} />;
}
function ReplayApp() {
  const [view, setView] = useState<View>(initialView);
  return <Workspace session={useReplayInvestigation(view === "investigate")} view={view} setView={setView} />;
}

function Workspace({ session, view, setView }: { session: Session; view: View; setView: (v: View) => void }) {
  const live = session.mode === "live" ? session : null;
  const recorded = session.mode === "replay" ? session : null;
  const { current, ready, error } = session;
  const history = live?.history || null;
  const draft = live?.draft || "";
  const sending = live?.sending || false;
  const replay = recorded?.replay || null;
  const scenario = recorded?.scenario || 0;
  const turnIndex = recorded?.turnIndex || 0;
  const closeHistory = () => live?.dismissHistory();
  const setDraft = (value: string) => live?.setDraft(value);
  const setScenario = (value: number) => recorded?.setScenario(value);
  const setTurnIndex = (value: number) => recorded?.setTurnIndex(value);
  const action = async (fn: () => Promise<void>) => { if (live) await live.action(fn); };
  const [discardTarget, setDiscardTarget] = useState<string | null>(null);
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
  const [evidence, setEvidence] = useState<Figure | Answer | null>(null);
  const [evidencePresence, setEvidencePresence] = useState(false);
  const [evidenceOrigin, setEvidenceOrigin] = useState<SurfaceOrigin>(null);
  const [clock, setClock] = useState(Date.now());
  const [deleteTarget, setDeleteTarget] = useState<Investigation | null>(null);
  const [deleteOrigin, setDeleteOrigin] = useState<SurfaceOrigin>(null);
  const [discardOrigin, setDiscardOrigin] = useState<SurfaceOrigin>(null);
  const [historyOrigin, setHistoryOrigin] = useState<SurfaceOrigin>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyQuery, setHistoryQuery] = useState("");
  const [anchor, setAnchor] = useState<string | null>(() => {
    const hash = location.hash.slice(1);
    return hash.includes("/") ? hash.split("/")[1] : null;
  });
  const ledger = useLedger();
  const prompt = useRef<HTMLTextAreaElement>(null);
  const pane = useRef<HTMLElement>(null);
  const selectedRef = useRef<HTMLElement | null>(null);
  const evidenceScroll = useRef({ narrow: 0, wide: 0 });
  const desktopEvidenceOpenRef = useRef(false);
  const autoSeen = useRef("");
  const t = (ko: string, en: string) => (lang === "ko" ? ko : en);
  const reduceMotion = useReducedMotion();
  const dark = theme === "system" ? systemDark : theme === "dark";
  const desktopEvidenceOpen = Boolean(evidence && !narrow);
  desktopEvidenceOpenRef.current = desktopEvidenceOpen;
  const active = current?.turns.some(unresolved) || false;
  const runtimeBusy = live?.running || false;
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
    const change = () => {
      setNarrow(media.matches);
    };
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    const value = dark ? "dark" : "light";
    document.documentElement.dataset.theme = value;
  }, [dark]);
  useEffect(() => {
    document.documentElement.lang = lang;
    localStorage.setItem("filing-language", lang);
  }, [lang]);
  useEffect(() => {
    if (view === "investigate") return;
    const hash = view === "home" ? "" : "#" + view + (anchor ? "/" + anchor : "");
    window.history.replaceState(null, "", location.pathname + location.search + hash);
  }, [view, anchor]);
  useEffect(() => {
    setEvidence(null);
    if (!anchor) {
      pane.current?.scrollTo({ top: 0 });
      window.scrollTo({ top: 0 });
    }
  }, [view]);
  useEffect(() => {
    if (view !== "investigate") return;
    const turn = current?.turns[turnIndex];
    setEvidence(replayMode && !narrow && turnIndex === 0
      ? turn?.answer?.figures[0] || turn?.answer || null : null);
    setEvidenceOrigin(null);
    selectedRef.current = null;
  }, [current?.id, scenario, turnIndex, view]);
  useEffect(() => {
    if (desktopEvidenceOpen) setEvidencePresence(true);
  }, [desktopEvidenceOpen]);
  useEffect(() => {
    if (replayMode || !current) return;
    const last = current.turns.at(-1);
    if (last?.status === "complete" && last.answer?.reason_code &&
        last.answer.operation !== "clarify" && autoSeen.current !== last.id) {
      autoSeen.current = last.id;
      setEvidence(last.answer);
    }
  }, [current]);
  function go(destination: Destination) {
    if (destination.view === "investigate") {
      if (recorded) setScenario(destination.scenario);
      setAnchor(null);
      setView("investigate");
      if (live) requestAnimationFrame(() => prompt.current?.focus());
      return;
    }
    setAnchor(destination.anchor === "top" ? null : destination.anchor);
    setView(destination.view);
    if (destination.view === "guide" && destination.anchor !== "top") {
      requestAnimationFrame(() => document.getElementById(destination.anchor)?.scrollIntoView({ block: "start" }));
    }
  }
  async function newInvestigation(text = "") {
    if (!live) return;
    setView("investigate");
    await live.newInvestigation(text);
    requestAnimationFrame(() => prompt.current?.focus());
  }
  async function submit(question = draft, retry?: Turn) {
    await live?.submit(question, lang, retry);
  }
  function inspect(value: Figure | Answer, e?: React.MouseEvent<HTMLElement>) {
    if (!("id" in value) || selected !== value.id) {
      evidenceScroll.current = { narrow: 0, wide: 0 };
    }
    selectedRef.current = e?.currentTarget || null;
    setEvidenceOrigin(originOf(e?.currentTarget));
    setEvidence(value);
  }
  function closeEvidence() {
    setEvidence(null);
    requestAnimationFrame(() => selectedRef.current?.focus());
  }
  function evidenceContent(content: React.ReactNode, layout: "narrow" | "wide") {
    return (
      <div
        className="evidence-content"
        ref={(node) => {
          if (node) node.scrollTop = evidenceScroll.current[layout];
        }}
        onScroll={(e) => {
          const isNarrow = matchMedia("(max-width: 850px)").matches;
          if ((layout === "narrow") === isNarrow) {
            evidenceScroll.current[layout] = e.currentTarget.scrollTop;
          }
        }}
      >
        {content}
      </div>
    );
  }
  const turns = current
    ? replayMode
      ? current.turns.slice(0, turnIndex + 1)
      : current.turns
    : [];
  const selected = "id" in (evidence || {}) ? (evidence as Figure).id : null;
  const context = current?.pending || current?.accepted;
  const modalOpen = Boolean((narrow && evidence) || history || discardTarget || deleteTarget);
  const followUps = (() => {
    if (!context || context.companies.length !== 1 || !context.metric) return [];
    const company = context.companies[0];
    const period = context.periods.length === 1 ? context.periods[0] : null;
    const nextMetric = context.metric === "revenue"
      ? t("영업이익은?", "What about operating income?")
      : t("매출액은?", "What about revenue?");
    const alternatePeriod = company === "Samsung"
      ? (period === "2022" ? "2023" : period === "2023" ? "2022" : null)
      : company === "Microsoft"
        ? (period === "2023" ? "2024" : period === "2024" ? "2023" : null)
        : null;
    return alternatePeriod
      ? [nextMetric, t(`${alternatePeriod}년은?`, `What about FY${alternatePeriod}?`)]
      : [nextMetric];
  })();
  const sourceView = evidence && <EvidenceBody evidence={evidence} lang={lang} t={t} />;
  const tabs: [View, string][] = [
    ...(replayMode ? [["home", t("소개", "Overview")] as [View, string]] : []),
    ["investigate", replayMode ? t("녹화된 조사", "Recorded runs") : t("조사", "Investigate")],
    ["ledger", t("수치 장부", "Ledger")],
    ["guide", t("공시 가이드", "Guide")],
  ];
  const answerLang = (turn: Turn) => (replayMode ? lang : turn.language);

  function renderTurn(turn: Turn, index: number) {
    const a = turn.answer;
    const al = answerLang(turn);
    const note = replayMode ? scenarios[scenario]?.turns[index] : undefined;
    return (
      <article className="turn" key={turn.id} data-turn={turn.id}>
        <div className="question">
          <div>
            <p className="label">{t(`질문 ${index + 1}`, `Question ${index + 1}`)}</p>
            <h2>
              {replayMode && lang === "en" && turn.question_en
                ? turn.question_en
                : turn.question}
            </h2>
            {replayMode && lang === "en" && turn.question_en && (
              <details className="original-question">
                <summary>Translated · asked in Korean</summary>
                <p lang="ko">{turn.question}</p>
              </details>
            )}
          </div>
          {!replayMode && (
            <button
              className="quiet"
              disabled={active}
              onClick={() =>
                action(() => newInvestigation(turn.question))
              }
            >
              {t("고쳐서 새로 묻기", "Edit as new")}
            </button>
          )}
        </div>
        {note && <p className="turn-note"><span className="label">{t("볼 것", "Notice")}</span>{pick(note, lang)}</p>}
        {a && (
          <div className="answer" lang={al}>
            <p className="answer-sentence">{a[al === "ko" ? "answer_ko" : "answer_en"]}</p>
            {a.figures.length ? (
              <table className="ledger-table answer-figures">
                <caption className="sr-only">{t("답에 쓰인 수치", "Figures in this answer")}</caption>
                <tbody>
                  {a.figures.map((f) => (
                    <tr key={f.id} className={selected === f.id ? "selected" : undefined}>
                      <th scope="row">
                        <span className="figure-company">{label("company", f.company, al)}</span>
                        <span className="figure-meta">{periodLabel(f.period, al)} · {label("metric", f.metric, al)}</span>
                      </th>
                      <td className="num">
                        <button
                          className={"figure-value" + (selected === f.id ? " selected" : "")}
                          onClick={(e) => inspect(f, e)}
                          aria-label={`${label("company", f.company, lang)} ${periodLabel(f.period, lang)} ${label("metric", f.metric, lang)} ${compact(f.value, f.currency, al)}, ${t("원문 근거 보기", "inspect source")}`}
                        >
                          {compact(f.value, f.currency, al)}
                        </button>
                      </td>
                      <td className="badge-cell"><SourceBadge regulator={f.source.regulator} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="missing">
                <strong aria-hidden="true">–</strong>
                <span>{t("검증된 수치 없음", "No verified figure")}</span>
              </div>
            )}
            {a.calculated.map((c, i) => {
              const inputs = c.inputs.map((id) => a.figures.find((f) => f.id === id)!);
              return (
                <div className="calc-block" key={i}>
                  <p className="label">{t("계산 · 코드가 수행", "Calculation · done by code")}</p>
                  <p className="calc-result">{signedPercent(c.percentage_change)}</p>
                  <p className="calc-formula">
                    ({periodLabel(inputs[0]?.period || "", al)} − {periodLabel(inputs[1]?.period || "", al)}) ÷ {periodLabel(inputs[1]?.period || "", al)} × 100
                  </p>
                  <p className="calc-detail num">
                    {t("차이", "Difference")} {exact(c.absolute_change)} {c.currency}
                  </p>
                  <div className="calc-inputs">
                    {inputs.map((f) => (
                      <button key={f.id} className="quiet" onClick={(e) => inspect(f, e)}>
                        {periodLabel(f.period, al)} · {exact(f.value)} {f.currency}
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
            {a.reason_code && a.operation !== "clarify" && (
              <button onClick={(e) => inspect(a, e)}>
                {t("확인한 범위 보기", "See what was checked")}
              </button>
            )}
            {a.operation === "clarify" &&
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
                      disabled={active || runtimeBusy || current?.saved}
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
        {!replayMode && turn.status === "saving" && <p role="status">{t("결과를 기록하는 중…", "Saving result…")}</p>}
        {!replayMode && turn.status === "storage_failed" && (
          <div className="storage-recovery" role="status">
            <p>{t("결과를 기록하지 못했습니다.", "This result couldn't be stored.")}</p>
            <p>{t("로컬 앱을 종료하면 기록되지 않은 결과가 사라질 수 있습니다.", "Closing the local app could lose this result.")}</p>
            <button onClick={() => action(async () => { if (current) await live?.recover(current.id); })}>
              {t("기록 다시 시도", "Retry storage")}
            </button>
            <button onClick={(e) => {
              setDiscardOrigin(originOf(e.currentTarget));
              setDiscardTarget(current!.id);
            }}>
              {t("기록되지 않은 결과 버리기", "Discard unstored result")}
            </button>
          </div>
        )}
        {turn.status === "discarded" && <p role="status">{t("기록되지 않은 결과를 버렸습니다. 이전 대화는 유지됩니다.", "Unstored result discarded. Earlier turns are preserved.")}</p>}
        {turn.error && !["storage_failed", "discarded"].includes(turn.status) && (
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
            {(() => {
              const seconds = turn.wall_seconds?.toFixed(2) ||
                (busy(turn)
                  ? Math.max(0, (clock - Date.parse(turn.created_at)) / 1000).toFixed(1)
                  : null);
              return seconds ? t(`${seconds}초`, `${seconds}s`) : "…";
            })()}
            {replayMode ? t(" · 녹화된 실제 시간", " · actual recorded time") : ""}
          </summary>
          <ol>
            {turn.steps.map((s) => (
              <li key={s.name}>
                <span>
                  {
                    (
                      {
                        interpret: t("질문 해석", "Interpret question"),
                        evidence: t("검증 자료 조회 및 계산", "Resolve evidence and calculate"),
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
                    stop_unconfirmed: t("중지 미확인", "Stop unconfirmed"),
                  } as Record<string, string>
                )[s.status] || s.status}{" "}
                <span className="num">
                  {s.seconds !== undefined
                    ? t(`${s.seconds.toFixed(2)}초`, `${s.seconds.toFixed(2)}s`)
                    : s.status === "running" && s.started_at
                      ? t(`${Math.max(0, (clock - Date.parse(s.started_at)) / 1000).toFixed(1)}초`, `${Math.max(0, (clock - Date.parse(s.started_at)) / 1000).toFixed(1)}s`)
                      : ""}
                </span>{" "}
                {s.reused
                  ? t("(완료한 단계 재사용)", "(completed step reused)")
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
                  await live?.cancel(turn.id);
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
              disabled={active || runtimeBusy || current?.saved}
              onClick={() => submit(turn.question, turn)}
            >
              {t("한 번 다시 시도", "Retry once")}
            </button>
          )}
      </article>
    );
  }

  function liveStart() {
    const examples = lang === "ko"
      ? ["삼성전자 2023년과 2022년 매출액을 비교해 줘", "네이버 2023년 영업이익은?", "Microsoft 2024년과 2023년 당기순이익을 비교해 줘"]
      : ["Compare Samsung revenue in FY2023 and FY2022.", "What was NAVER's operating income in FY2023?", "Compare Microsoft net income in FY2024 and FY2023."];
    const fill = (q: string) => { setDraft(q); prompt.current?.focus(); };
    return (
      <div className="page start">
        <p className="label">{t("로컬 조사 · 검증된 과거 공시", "Local investigation · verified historical filings")}</p>
        <h1>{t("무엇을 확인할까요?", "What would you like to check?")}</h1>
        <p className="lede">
          {t(
            "회사, 지표, 회계연도를 넣어 물어보세요. 이어서 묻는 질문은 앞의 문맥을 이어받습니다.",
            "Name a company, metric and fiscal year. Follow-up questions keep the earlier context.",
          )}
        </p>
        <section className="block" aria-labelledby="supported-examples">
          <h2 id="supported-examples">{t("이렇게 시작해 보세요", "Try one of these")}</h2>
          <ul className="example-list">
            {examples.map((q) => <li key={q}><button onClick={() => fill(q)}>{q}</button></li>)}
            <li>
              <button onClick={() => fill(t("삼성전자 2023년 연구개발비는?", "What was Samsung's R&D expense in FY2023?"))}>
                {t("삼성전자 2023년 연구개발비는?", "What was Samsung's R&D expense in FY2023?")}
              </button>
              <span className="muted">
                {t("검증 모음에 없는 지표입니다. 숫자를 만들지 않고 확인한 범위를 보여 줍니다.", "Not in the verified collection. Shows the checked scope instead of a number.")}
              </span>
            </li>
          </ul>
        </section>
        <p className="note">
          {t("지원 범위와 수치 전체는 ", "See the full coverage in the ")}
          <button className="link" onClick={() => go({ view: "ledger", anchor: "top" })}>{t("수치 장부", "ledger")}</button>
          {t("에서 볼 수 있습니다.", ".")}
        </p>
      </div>
    );
  }

  function investigation() {
    if (replayMode && !replay) {
      return (
        <div className="page">
          <p role="status">
            {error
              ? t("녹화 자료를 불러오지 못했습니다.", "The recording could not be loaded.")
              : t("녹화 자료를 불러오는 중입니다.", "Loading the recording.")}
          </p>
          {error && <button onClick={() => location.reload()}>{t("다시 불러오기", "Reload recording")}</button>}
        </div>
      );
    }
    if (!replayMode && turns.length === 0) return liveStart();
    const total = current?.turns.length || 1;
    return (
      <div className="page investigation">
        {replayMode && replay && (
          <nav className="scenario-picker" aria-label={t("녹화된 조사 선택", "Choose a recorded investigation")}>
            {replay.investigations.map((_, i) => (
              <button
                key={i}
                aria-pressed={scenario === i}
                onClick={() => { setScenario(i); setTurnIndex(0); }}
              >
                <span className="label">{t(`조사 ${i + 1}`, `Run ${i + 1}`)}</span>
                <strong>{scenarios[i] ? pick(scenarios[i].title, lang) : i + 1}</strong>
              </button>
            ))}
          </nav>
        )}
        <header className="investigation-head">
          <h1>
            {replayMode
              ? [
                  t("삼성전자 매출, 한 해 사이 얼마나 변했나", "How much did Samsung's revenue change in a year?"),
                  t("한 마디로 회사만 바꿔 묻기", "Switching companies in one follow-up"),
                  t("검증된 근거가 없을 때", "When verified evidence is missing"),
                ][scenario]
              : t("공시 조사", "Filing investigation")}
          </h1>
          {replayMode && scenarios[scenario] && <p className="lede">{pick(scenarios[scenario].notice, lang)}</p>}
          {current?.saved && !replayMode && (
            <p className="muted">{t("저장됨 · 원본 보존", "Saved · original preserved")}</p>
          )}
          {!replayMode && current?.lineage && (
            <p className="muted">
              {current.lineage.mode === "continue"
                ? t("저장본에서 이어진 새 조사 · 원본 근거 유지", "New investigation continued from saved results · original evidence")
                : t("새 조사 · 현재 검증 자료 사용", "New investigation · current verified evidence")}
            </p>
          )}
        </header>
        {turns.map(renderTurn)}
        {replayMode && (
          <nav className="stepper" aria-label={t("질문 이동", "Question navigation")}>
            <button disabled={turnIndex === 0} onClick={() => setTurnIndex(turnIndex - 1)}>
              <span aria-hidden="true">← </span>{t("이전 질문", "Previous question")}
            </button>
            <span className="num" aria-live="polite">{t(`질문 ${turnIndex + 1} / ${total}`, `Question ${turnIndex + 1} of ${total}`)}</span>
            {turnIndex < total - 1 ? (
              <button className="primary" onClick={() => setTurnIndex(turnIndex + 1)}>
                {t("다음 질문", "Next question")}<span aria-hidden="true"> →</span>
              </button>
            ) : scenario < (replay?.investigations.length || 1) - 1 ? (
              <button className="primary" onClick={() => setScenario(scenario + 1)}>
                {t("다음 조사", "Next run")}<span aria-hidden="true"> →</span>
              </button>
            ) : (
              <button className="primary" onClick={() => go({ view: "ledger", anchor: "top" })}>
                {t("수치 장부 보기", "Open the ledger")}<span aria-hidden="true"> →</span>
              </button>
            )}
          </nav>
        )}
      </div>
    );
  }

  return (
    <div className="app-shell" data-theme={dark ? "dark" : "light"}>
      <a className="skip" href="#main-pane">
        {t("본문으로 이동", "Skip to content")}
      </a>
      <div className="sr-only" aria-live="polite">
        {active
          ? t("질문을 처리하고 있습니다.", "Processing the question.")
          : current?.turns.at(-1)?.status === "complete"
            ? t("답변이 준비되었습니다.", "The answer is ready.")
            : ""}
      </div>
      <header className="topbar" inert={modalOpen || undefined}>
        <a
          className="wordmark"
          href={replayMode ? "./index.html" : "/"}
          onClick={(e) => { e.preventDefault(); setView(replayMode ? "home" : "investigate"); }}
        >
          <span className="family-mark" aria-hidden="true">
            <img className="mark-light" src="./family-mark-light.png" alt="" />
            <img className="mark-dark" src="./family-mark-dark.png" alt="" />
          </span>
          <span>Filing Agent</span>
        </a>
        <nav className="tabs" aria-label={t("주요 메뉴", "Primary navigation")}>
          {tabs.map(([key, name]) => (
            <button key={key} aria-current={view === key ? "page" : undefined} onClick={() => { setAnchor(null); setView(key); }}>
              {name}
            </button>
          ))}
        </nav>
        <div className="controls">
          {!replayMode && (
            <>
              <button
                onClick={() => action(() => newInvestigation())}
                disabled={sending || !ready}
              >
                {t("새 조사", "New")}
              </button>
              <button
                onClick={(e) => {
                  setHistoryOrigin(originOf(e.currentTarget));
                  setHistoryLoading(true);
                  void action(async () => {
                    try { await live?.openHistory(); }
                    finally { setHistoryLoading(false); }
                  });
                }}
              >
                {t("기록", "History")}
              </button>
            </>
          )}
          <div className="languages" role="group" aria-label={t("언어", "Language")}>
            <button lang="ko" aria-pressed={lang === "ko"} onClick={() => setLang("ko")}>한국어</button>
            <button lang="en" aria-pressed={lang === "en"} onClick={() => setLang("en")}>English</button>
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
              document.documentElement.dataset.theme = v;
              setTheme(v);
              localStorage.setItem("filing-theme", v);
            }}
          >
            <span aria-hidden="true">{dark ? "☀" : "☾"}</span>
          </button>
        </div>
      </header>
      <main
        inert={modalOpen || undefined}
        className={
          desktopEvidenceOpen || evidencePresence
            ? "workspace with-evidence"
            : "workspace"
        }
      >
        <section
          className="main-pane"
          id="main-pane"
          ref={pane}
          aria-label={tabs.find(([key]) => key === view)?.[1]}
        >
          {view === "home" && <Home lang={lang} t={t} go={go} live={!replayMode} />}
          {view === "guide" && <Guide lang={lang} t={t} />}
          {view === "ledger" && (
            <Ledger lang={lang} t={t} inspect={inspect} selected={selected} data={ledger.data} failed={ledger.failed} anchor={anchor} />
          )}
          {view === "investigate" && investigation()}
          {view === "investigate" && !replayMode && (
            <div className="composer">
              {current && turns.length > 0 && !active && (
                <div className="actions">
                  {!current.saved && (
                    <button
                      onClick={() =>
                        action(async () => { await live?.save(current.id); })
                      }
                    >
                      {t("조사 저장", "Save investigation")}
                    </button>
                  )}
                  {current.saved &&
                    ["continue", "refresh"].map((mode) => (
                      <button
                        className={mode === "continue" ? "primary" : undefined}
                        key={mode}
                        onClick={() =>
                          action(async () => {
                            await live?.fork(current.id, mode);
                          })
                        }
                      >
                        {mode === "continue"
                          ? t("원본 근거로 계속", "Continue with original evidence")
                          : t("현재 검증 자료로 새 조사", "New investigation with current data")}
                      </button>
                    ))}
                </div>
              )}
              {current?.saved && (
                <p className="muted">{t("저장본은 그대로 보존됩니다. 현재 검증 자료로 시작해도 새 공시를 내려받지는 않습니다.", "The saved result stays unchanged. Starting with current verified data does not download new filings.")}</p>
              )}
              {context && (
                <div className="context">
                  {current?.pending
                    ? t("확인 중인 문맥", "Pending clarification")
                    : t("이어받는 문맥", "Carried context")}
                  {context.companies.map((c) => (
                    <span className="context-chip" key={c}>
                      {label("company", c, lang)}
                    </span>
                  ))}
                  <span className="context-chip">
                    {context.metric
                      ? label("metric", context.metric, lang)
                      : "–"}
                  </span>
                  {context.periods.map((p) => (
                    <span className="context-chip" key={p}>
                      {periodLabel(p, lang)}
                    </span>
                  ))}
                </div>
              )}
              {runtimeBusy && !current?.turns.some(busy) && <p role="status">{t("다른 조사가 실행 중입니다. 완료되면 질문할 수 있습니다.", "Another investigation is running. You can ask when it finishes.")}</p>}
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
                  <label htmlFor="prompt" className="sr-only">
                    {t("공시에 대해 질문하기", "Ask about a filing")}
                  </label>
                  {followUps.length > 0 && (
                    <div className="follow-ups" aria-label={t("다음 질문 예시", "Suggested follow-up questions")}>
                      <span>{t("이어서 묻기", "Ask next")}</span>
                      {followUps.map((question) => (
                        <button key={question} type="button" onClick={() => { setDraft(question); prompt.current?.focus(); }}>
                          {question}
                        </button>
                      ))}
                    </div>
                  )}
                  <div className="prompt-row">
                    <textarea
                      id="prompt"
                      disabled={!ready || sending}
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
                        "예: 네이버 2023년 영업이익은?",
                        "e.g. What was NAVER's operating income in FY2023?",
                      )}
                    />
                    <button
                      className="send primary"
                      disabled={!ready || sending || active || runtimeBusy || !draft.trim()}
                      type="submit"
                    >
                      {t("질문", "Ask")}
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
          {view !== "investigate" || replayMode ? (
            <footer className="site-footer">
              <span>Filing Agent</span>
              {replayMode && <a href={lang === "ko" ? "./engineering-ko.html" : "./engineering-en.html"}>{t("만든 과정과 검증 기록", "Engineering notes and verification")}</a>}
              <a href="https://mhju0.github.io/filing-digest/">Filing Digest ↗</a>
              <span className="muted">{t("투자 권유가 아닙니다.", "Not investment advice.")}</span>
            </footer>
          ) : null}
        </section>
        <AnimatePresence
          initial={false}
          onExitComplete={() => {
            if (!desktopEvidenceOpenRef.current) setEvidencePresence(false);
          }}
        >
          {desktopEvidenceOpen && (
            <DesktopEvidence
              key="desktop-evidence"
              title={t("근거", "Evidence")}
              close={closeEvidence}
              origin={evidenceOrigin}
              reduceMotion={reduceMotion}
            >
              {evidenceContent(sourceView, "wide")}
            </DesktopEvidence>
          )}
        </AnimatePresence>
      </main>
      <AnimatePresence initial={false}>
        {evidence && narrow && (
          <Modal key="mobile-evidence" title={t("근거", "Evidence")} close={closeEvidence} origin={evidenceOrigin} evidenceSurface>
            {evidenceContent(sourceView, "narrow")}
          </Modal>
        )}
      </AnimatePresence>
      <AnimatePresence initial={false}>
      {history && (
        <Modal
          key="history"
          title={t("기록", "History")}
          close={closeHistory}
          origin={historyOrigin}
          active={!deleteTarget}
        >
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
              "일반 조사는 30일간 활동이 없으면 만료됩니다. 저장한 조사는 삭제할 때까지 보존됩니다.",
              "Ordinary investigations expire after 30 idle days. Saved investigations remain until deleted.",
            )}
          </p>
          {historyLoading ? (
            <p role="status">{t("기록을 불러오는 중입니다.", "Loading history.")}</p>
          ) : history.length > 0 && historyQuery && !history.some((inv) => inv.turns.some((turn) => turn.question.toLowerCase().includes(historyQuery.toLowerCase()))) ? (
            <p>{t("일치하는 조사가 없습니다.", "No matching investigations.")}</p>
          ) : history.length === 0 ? (
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
                      live?.select(inv);
                      setView("investigate");
                      closeHistory();
                    }}
                  >
                    {inv.turns[0]?.question ||
                      t("새 조사", "New investigation")}
                    <small>
                      {inv.turns.some(turn => turn.status === "storage_failed")
                        ? t("기록 실패", "Storage failed")
                        : inv.turns.some(busy) ? t("실행 중", "Running")
                        : inv.saved ? t("저장됨", "Saved") : t("최근", "Recent")} ·{" "}
                      {new Date(inv.created_at).toLocaleDateString(lang)}
                    </small>
                  </button>
                  <button
                    aria-label={t("이 조사 삭제", "Delete this investigation")}
                    disabled={inv.turns.some(unresolved)}
                    onClick={(e) => {
                      setDeleteOrigin(originOf(e.currentTarget));
                      setDeleteTarget(inv);
                    }}
                  >
                    {t("삭제", "Delete")}
                  </button>
                </div>
              ))
          )}
        </Modal>
      )}
      </AnimatePresence>
      <AnimatePresence initial={false}>
      {discardTarget && (
        <Modal key="discard" title={t("기록되지 않은 결과 버리기", "Discard unstored result")} close={() => setDiscardTarget(null)} origin={discardOrigin}>
          <p>{t("이 결과를 버립니다. 이전에 기록된 대화와 문맥은 유지됩니다. 버림 처리를 기록할 때까지 새 질문은 제한됩니다.", "Discard this result and preserve earlier stored turns and context. New turns remain blocked until the discard is recorded.")}</p>
          <button onClick={() => action(async () => {
            await live?.recover(discardTarget, true);
            setDiscardTarget(null);
          })}>{t("버리기 확인", "Confirm discard")}</button>
          {error && <p role="alert">{error}</p>}
        </Modal>
      )}
      </AnimatePresence>
      <AnimatePresence initial={false}>
      {deleteTarget && (
        <Modal
          key="delete"
          title={t("조사 삭제", "Delete investigation")}
          close={() => setDeleteTarget(null)}
          origin={deleteOrigin}
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
                await live?.remove(deleteTarget.id);
                setDeleteTarget(null);
              })
            }
          >
            {t("삭제 확인", "Confirm deletion")}
          </button>
        </Modal>
      )}
      </AnimatePresence>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <MotionConfig reducedMotion="user">
    {replayMode ? <ReplayApp /> : <LiveApp />}
  </MotionConfig>,
);
