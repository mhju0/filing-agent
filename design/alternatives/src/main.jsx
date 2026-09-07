import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  revenue,
  fragment,
  percentage,
  exactPercentage,
  formatOriginal,
  displayValue,
  dictionary,
} from "./data";
import "./styles.css";

const variant = location.pathname.match(/\/([abc])\.html$/)?.[1] || "a";
const names = { a: "Reading first", b: "Ledger", c: "Card stack" };
function Icon({ name, ...props }) {
  const paths = {
    close: "m6 6 12 12M18 6 6 18",
    plus: "M12 5v14M5 12h14",
    history: "M4 5v5h5M4.4 10a8 8 0 1 1 1.7 8M12 7v5l3 2",
    arrow: "M12 19V5m-6 6 6-6 6 6",
    check: "m5 12 4 4L19 6",
    document: "M7 3h7l4 4v14H6V3h1m7 0v5h4M9 12h6M9 16h6",
    down: "m6 9 6 6 6-6",
    menu: "M5 12h.01M12 12h.01M19 12h.01",
  };
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...props}
    >
      <path d={paths[name]} />
    </svg>
  );
}

function App() {
  const [lang, setLang] = useState(() => {
    try {
      return localStorage.getItem("filing-design-language") || "ko";
    } catch {
      return "ko";
    }
  });
  const [theme, setTheme] = useState(
    document.documentElement.dataset.theme || "light",
  );
  const [selected, setSelected] = useState("2023");
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [fullSheet, setFullSheet] = useState(false);
  const [formulaOpen, setFormulaOpen] = useState(false);
  const [translated, setTranslated] = useState(false);
  const [modal, setModal] = useState(null);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState(false);
  const [mobile, setMobile] = useState(
    matchMedia("(max-width: 760px)").matches,
  );
  const [changed, setChanged] = useState(true);
  const dialog = useRef(null),
    evidence = useRef(null),
    prompt = useRef(null),
    lastFigure = useRef(null),
    drag = useRef(null);
  const t = dictionary[lang];
  const sourceRow = revenue.find((row) => row.period === selected);

  useEffect(() => {
    const media = matchMedia("(max-width: 760px)");
    const update = () => setMobile(media.matches);
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    document.documentElement.lang = lang;
    try {
      localStorage.setItem("filing-design-language", lang);
    } catch {
      /* Private browsing may disable storage. */
    }
  }, [lang]);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("filing-design-theme", theme);
    } catch {
      /* Theme remains usable in memory. */
    }
  }, [theme]);
  useEffect(() => {
    if (modal) dialog.current?.showModal();
    else dialog.current?.close();
  }, [modal]);
  useEffect(() => {
    if (!mobile || !evidenceOpen) return;
    const panel = evidence.current;
    panel?.querySelector("button")?.focus({ preventScroll: true });
    const trap = (event) => {
      if (event.key === "Escape") {
        closeEvidence();
        return;
      }
      if (event.key !== "Tab") return;
      const controls = [...panel.querySelectorAll("button, a, summary")].filter(
        (el) => el.getClientRects().length,
      );
      const first = controls[0],
        last = controls.at(-1);
      if (!panel.contains(document.activeElement)) {
        event.preventDefault();
        first.focus();
      } else if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", trap);
    return () => document.removeEventListener("keydown", trap);
  }, [mobile, evidenceOpen]);

  function closeEvidence() {
    setEvidenceOpen(false);
    requestAnimationFrame(() => {
      const target = lastFigure.current?.isConnected
        ? lastFigure.current
        : document.querySelector(`.figure-button[aria-label^="${selected}"]`);
      target?.focus({ preventScroll: true });
    });
  }
  function inspect(period, event) {
    const opener = event.currentTarget;
    lastFigure.current = opener;
    const before = opener.getBoundingClientRect().top;
    setSelected(period);
    setEvidenceOpen(true);
    setTranslated(false);
    requestAnimationFrame(() => {
      if (!mobile)
        document
          .querySelector(".conversation-scroll")
          .scrollBy(0, opener.getBoundingClientRect().top - before);
    });
  }
  function Figure({ row, hero = false }) {
    return (
      <button
        key={row.period}
        className={`figure-button ${hero ? "hero-reported" : ""} ${evidenceOpen && selected === row.period ? "selected" : ""}`}
        onClick={(event) => inspect(row.period, event)}
        aria-label={`${row.period} ${t.metric} ${displayValue(row, lang)} · ${t.evidence}`}
        aria-pressed={evidenceOpen && selected === row.period}
      >
        <span className="figure-number">
          ≈ {displayValue(row, lang).replace(" trillion KRW", "")}
          {lang === "en" && <span className="figure-unit">trillion KRW</span>}
        </span>
        <span className="figure-period">· {row.period}</span>
        <span className="citation">
          <Icon name="document" />
        </span>
      </button>
    );
  }
  const CalcBadge = () => (
    <button
      className="calc-badge"
      aria-expanded={formulaOpen}
      aria-controls="formula"
      onClick={() => setFormulaOpen(!formulaOpen)}
    >
      {t.calc}
      <Icon name="down" />
    </button>
  );
  const Formula = () =>
    formulaOpen && (
      <section id="formula" className="formula-box" aria-label={t.formula}>
        <div className="flex items-center justify-between gap-3">
          <h3>{t.formula}</h3>
          <span className="muted">%</span>
        </div>
        <p className="formula-expression">
          ({formatOriginal(revenue[0].value)} −{" "}
          {formatOriginal(revenue[1].value)})<br />÷{" "}
          {formatOriginal(revenue[1].value)} × 100 = ≈ {exactPercentage}%
        </p>
        <p className="muted text-sm">{t.formulaNote}</p>
        <p className="small-label mt-4">{t.inputs}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          {revenue.map((row) => Figure({ row }))}
        </div>
      </section>
    );
  const FigureTable = () => (
    <table className="figure-table">
      <caption className="sr-only">{t.title}</caption>
      <thead>
        <tr>
          <th scope="col">{t.period}</th>
          <th scope="col">{t.value}</th>
          <th scope="col">{t.source}</th>
        </tr>
      </thead>
      <tbody>
        {revenue.map((row) => (
          <tr key={row.period}>
            <th scope="row">{row.period}</th>
            <td>{Figure({ row })}</td>
            <td>
              <button
                className="source-chip"
                onClick={(event) => inspect(row.period, event)}
              >
                <span className="citation-number">
                  {row.period === "2023" ? "1" : "2"}
                </span>
                <span>{t.report}</span>
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
  const Explanation = () => (
    <details className="explanation">
      <summary>
        {t.explanation}
        <Icon name="down" />
      </summary>
      <p>{t.explanationText}</p>
    </details>
  );
  const Limitations = () => (
    <div className="limitations">
      <span className="small-label">{t.limits}</span>
      <p>{t.limitation}</p>
    </div>
  );
  const Trail = () => (
    <section className="trail" aria-label={t.trail}>
      <div className="trail-heading">
        <h3>{t.trail}</h3>
        <span>{t.trailNote}</span>
      </div>
      <ol>
        {t.stages.map((stage) => (
          <li key={stage}>
            <Icon name="check" />
            <span>{stage}</span>
          </li>
        ))}
      </ol>
      <p>
        <Icon name="document" />
        2023 · 2022 &nbsp; / &nbsp; {t.stageTarget}
      </p>
    </section>
  );

  return (
    <div
      className={`app variant-${variant} ${evidenceOpen ? "with-evidence" : ""}`}
    >
      <div
        className="review-bar"
        inert={mobile && evidenceOpen ? true : undefined}
      >
        <div>
          <span className="review-label">{t.prototype}</span>
          <span className="review-detail">{t.prototypeDetail}</span>
        </div>
        <nav aria-label="Design alternatives">
          {Object.entries(names).map(([key, name]) => (
            <a
              key={key}
              href={`./${key}.html`}
              aria-current={variant === key ? "page" : undefined}
            >
              <b>{key.toUpperCase()}</b>
              <span>{name}</span>
            </a>
          ))}
        </nav>
      </div>
      <header
        className="topbar"
        inert={mobile && evidenceOpen ? true : undefined}
      >
        <a
          className="wordmark"
          href={`./${variant}.html`}
          aria-label="Filing Agent"
        >
          filing<span>agent</span>
          <i aria-hidden="true">↗</i>
        </a>
        <div className="topbar-actions">
          <button onClick={() => setModal("new")}>
            <Icon name="plus" />
            <span>{t.new}</span>
          </button>
          <button onClick={() => setModal("history")}>
            <Icon name="history" />
            <span>{t.history}</span>
          </button>
          <button
            className="icon-button"
            aria-label={t.settings}
            onClick={() => setModal("settings")}
          >
            <Icon name="menu" />
          </button>
        </div>
      </header>
      <div className="workspace">
        <main
          className="conversation"
          inert={mobile && evidenceOpen ? true : undefined}
        >
          <div className="conversation-scroll">
            <div className="investigation-heading">
              <p className="small-label">
                {t.eyebrow} <span>01</span>
              </p>
              <h1>{t.title}</h1>
              <p className="muted">{t.comparison}</p>
            </div>
            <div className="question">
              <span className="small-label">{t.questionLabel}</span>
              <p>{t.question}</p>
            </div>
            <article className="answer" aria-label={t.answerLabel}>
              {variant === "a" && (
                <>
                  <div className="answer-intro">
                    <span className="small-label">{t.revenue}</span>
                    <div className="delta-heading">
                      <span className="hero-delta">
                        ≈ {percentage}
                        <small>%</small>
                      </span>
                      {CalcBadge()}
                    </div>
                    <h2>{t.answer}</h2>
                    <p className="muted text-sm">{t.delta} · 2023 / 2022</p>
                  </div>
                  {Formula()}
                  {FigureTable()}
                  {Explanation()}
                  {Limitations()}
                  {Trail()}
                </>
              )}
              {variant === "b" && (
                <>
                  <div className="ledger-label">
                    <h2>{t.revenue}</h2>
                    <span className="small-label">{t.reported}</span>
                  </div>
                  <div className="ledger-heroes">
                    {revenue.map((row) => (
                      <div key={row.period}>
                        <span className="small-label">{row.period}</span>
                        {Figure({ row, hero: true })}
                      </div>
                    ))}
                    <div className="ledger-change">
                      <span className="small-label">{t.delta}</span>
                      <strong>≈ {percentage}%</strong>
                      {CalcBadge()}
                    </div>
                  </div>
                  <p className="ledger-answer">{t.answer}</p>
                  {Formula()}
                  {FigureTable()}
                  {Explanation()}
                  {Limitations()}
                  {Trail()}
                </>
              )}
              {variant === "c" && (
                <>
                  <section className="stack-hero">
                    <div className="flex items-center justify-between gap-3">
                      <h2>{t.revenue}</h2>
                      <span className="small-label">2023 / 2022</span>
                    </div>
                    <div className="stack-value">
                      {Figure({ row: revenue[0], hero: true })}
                      <div className="stack-delta">
                        <strong>≈ {percentage}%</strong>
                        {CalcBadge()}
                      </div>
                    </div>
                    <p>{t.answer}</p>
                    {Formula()}
                  </section>
                  <section className="stack-section">
                    <h3>{t.reported}</h3>
                    {FigureTable()}
                  </section>
                  <section className="stack-section">{Explanation()}</section>
                  <section className="stack-section">{Limitations()}</section>
                  <section className="stack-section">{Trail()}</section>
                </>
              )}
            </article>
          </div>
          <div className="composer">
            <div className="context-row">
              <span className="sr-only">{t.context}</span>
              {[t.company, t.metric].map((label) => (
                <button
                  key={label}
                  className="context-chip"
                  onClick={() => setModal("context")}
                >
                  {label}
                </button>
              ))}
              <button
                className={`context-chip ${changed ? "changed" : ""}`}
                title={t.contextChanged}
                onClick={() => {
                  setChanged(false);
                  setModal("context");
                }}
              >
                2023{changed && <span aria-hidden="true">✓</span>}
              </button>
            </div>
            <form
              onSubmit={(event) => {
                event.preventDefault();
                setError(true);
              }}
            >
              <textarea
                ref={prompt}
                aria-label={t.prompt}
                placeholder={t.prompt}
                rows="1"
                value={draft}
                onChange={(event) => {
                  setDraft(event.target.value);
                  setError(false);
                }}
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault();
                    setError(true);
                  }
                }}
              />
              <button className="send-button" aria-label={t.send} type="submit">
                <Icon name="arrow" />
              </button>
            </form>
            {error ? (
              <p className="prompt-error" role="alert">
                {t.staticError}
              </p>
            ) : (
              <p className="prompt-hint">
                {t.promptHint}
                <span>{t.footnote}</span>
              </p>
            )}
          </div>
        </main>
        {evidenceOpen && (
          <aside
            ref={evidence}
            className={`evidence ${fullSheet ? "full-sheet" : ""}`}
            role={mobile ? "dialog" : "complementary"}
            aria-modal={mobile ? "true" : undefined}
            aria-label={t.evidence}
          >
            <div
              className="sheet-grip"
              onPointerDown={(event) => {
                drag.current = event.clientY;
                event.currentTarget.setPointerCapture(event.pointerId);
              }}
              onPointerUp={(event) => {
                if (
                  drag.current !== null &&
                  Math.abs(event.clientY - drag.current) > 30
                )
                  setFullSheet(event.clientY < drag.current);
                drag.current = null;
              }}
              aria-hidden="true"
            >
              <span />
            </div>
            <div className="evidence-top">
              <div className="flex items-center gap-2">
                <span className="citation-number">
                  {selected === "2023" ? "1" : "2"}
                </span>
                <h2>{t.evidence}</h2>
              </div>
              <div className="flex items-center">
                <button
                  className="sheet-expand"
                  onClick={() => setFullSheet(!fullSheet)}
                  aria-expanded={fullSheet}
                >
                  {fullSheet ? t.collapse : t.expand}
                </button>
                <button
                  className="icon-button"
                  aria-label={`${t.evidence} ${t.close}`}
                  onClick={closeEvidence}
                >
                  <Icon name="close" />
                </button>
              </div>
            </div>
            <div className="evidence-scroll">
              <div className="selected-evidence">
                <span className="small-label">{t.selected}</span>
                <p>
                  {t.metric} <strong>≈ {displayValue(sourceRow, lang)}</strong>
                  <span>· {selected}</span>
                </p>
              </div>
              <section className="excerpt-block">
                <div className="excerpt-label">
                  <span>{t.excerpt}</span>
                  <span>{t.excerptNote}</span>
                </div>
                {variant === "b" ? (
                  <div className="document-table" lang="ko">
                    <h3>{t.excerptTitle}</h3>
                    <p>{t.excerptCompany}</p>
                    <table>
                      <caption className="sr-only">
                        연결손익계산서 발췌 · 백만원
                      </caption>
                      <thead>
                        <tr>
                          <th>과목</th>
                          <th>제55기</th>
                          <th>제54기</th>
                        </tr>
                      </thead>
                      <tbody>
                        {fragment.map((row) => (
                          <tr key={row.label}>
                            <th scope="row">{row.label}</th>
                            {row.values.map((value, index) => (
                              <td key={index}>
                                {row.label === "매출액" &&
                                ["2023", "2022"][index] === selected ? (
                                  <mark>{formatOriginal(value)}</mark>
                                ) : (
                                  formatOriginal(value)
                                )}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <blockquote className="document-excerpt" lang="ko">
                    <p className="document-title">{t.excerptTitle}</p>
                    <p className="document-company">{t.excerptCompany}</p>
                    <div className="excerpt-line">
                      <span>
                        {selected === "2023" ? "제55기" : "제54기"} · 매출액
                      </span>
                      <mark>{formatOriginal(sourceRow.value)}</mark>
                      <span>백만원</span>
                    </div>
                    <div className="excerpt-secondary">
                      {selected === "2023" ? "제54기" : "제55기"} · 매출액{" "}
                      <span>
                        {formatOriginal(
                          revenue.find((row) => row.period !== selected).value,
                        )}{" "}
                        백만원
                      </span>
                    </div>
                  </blockquote>
                )}
                <button
                  className="text-button translation-toggle"
                  aria-expanded={translated}
                  onClick={() => setTranslated(!translated)}
                >
                  {t.translate}
                  <Icon name="down" />
                </button>
                {translated && (
                  <div className="translation">
                    <p className="small-label">{t.translated}</p>
                    <p lang="en">
                      Consolidated income statement. Samsung Electronics Co.,
                      Ltd. and its subsidiaries. Revenue ({selected}):{" "}
                      {formatOriginal(sourceRow.value)} million KRW.
                    </p>
                  </div>
                )}
              </section>
              <div className="metadata">
                <p>{t.metadata}</p>
                <div>
                  <span>{selected}</span>
                  <span>{t.basis}</span>
                  <span>{t.units}</span>
                </div>
              </div>
              <section className="reconciliation">
                <h3>{t.reconciliation}</h3>
                <p>
                  <span lang="ko">
                    {formatOriginal(sourceRow.value)} 백만원
                  </span>
                  <span className="conversion-arrow" aria-hidden="true">
                    →
                  </span>
                  <strong>≈ {displayValue(sourceRow, lang)}</strong>
                </p>
                <span className="muted text-sm">{t.rounding}</span>
              </section>
              <a
                className="original-link"
                href={sourceRow.source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <Icon name="document" />
                {t.openSource}
              </a>
              <p className="source-note">{t.sourceNote}</p>
              <div className="evidence-footnote">
                <span>{t.source}</span>
                <p>{t.limitation}</p>
              </div>
            </div>
          </aside>
        )}
      </div>
      <dialog
        ref={dialog}
        className={`utility-dialog ${modal === "history" ? "history-dialog" : ""}`}
        onCancel={() => setModal(null)}
        onClick={(event) => {
          if (event.target === dialog.current) setModal(null);
        }}
        aria-label={
          modal === "settings"
            ? t.settings
            : modal === "history"
              ? t.historyTitle
              : modal === "new"
                ? t.newTitle
                : t.editingContext
        }
      >
        <div className="dialog-content">
          <div className="flex justify-between items-center gap-4">
            <h2>
              {modal === "settings"
                ? t.settings
                : modal === "history"
                  ? t.historyTitle
                  : modal === "new"
                    ? t.newTitle
                    : t.editingContext}
            </h2>
            <button
              className="icon-button"
              onClick={() => setModal(null)}
              aria-label={t.close}
            >
              <Icon name="close" />
            </button>
          </div>
          {modal === "settings" && (
            <>
              <div className="settings-group">
                <p>{t.language}</p>
                <div className="segmented">
                  <button
                    aria-pressed={lang === "ko"}
                    onClick={() => setLang("ko")}
                  >
                    한국어
                  </button>
                  <button
                    aria-pressed={lang === "en"}
                    onClick={() => setLang("en")}
                  >
                    English
                  </button>
                </div>
              </div>
              <div className="settings-group">
                <p>{t.theme}</p>
                <div className="segmented">
                  <button
                    aria-pressed={theme === "light"}
                    onClick={() => setTheme("light")}
                  >
                    {t.light}
                  </button>
                  <button
                    aria-pressed={theme === "dark"}
                    onClick={() => setTheme("dark")}
                  >
                    {t.dark}
                  </button>
                </div>
              </div>
              <p className="runtime-status">
                <span aria-hidden="true" />
                {t.runtime}
              </p>
            </>
          )}
          {modal === "history" && (
            <>
              <p className="muted my-5">{t.historyNote}</p>
              <button
                className="history-item"
                onClick={() => {
                  setModal(null);
                  setSelected("2023");
                  setEvidenceOpen(true);
                  document.querySelector(".conversation-scroll").scrollTo(0, 0);
                }}
              >
                <strong>{t.title}</strong>
                <span>{t.comparison}</span>
                <span>{t.reopen} ↗</span>
              </button>
            </>
          )}
          {modal === "new" && (
            <>
              <p className="muted my-5">{t.newNote}</p>
              <button
                className="primary-button"
                onClick={() => {
                  setModal(null);
                  setEvidenceOpen(false);
                  setDraft("");
                  setError(false);
                  requestAnimationFrame(() => prompt.current.focus());
                }}
              >
                {t.draft}
              </button>
            </>
          )}
          {modal === "context" && <p className="muted my-5">{t.contextNote}</p>}
        </div>
      </dialog>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
