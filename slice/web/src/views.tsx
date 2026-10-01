import React, { useEffect, useState } from "react";
import type { Answer, Figure } from "./types";
import { change, compact, exact, koreanUnits, ratio, signedPercent, type Lang } from "./format";
import { family, guide, pick, questionLibrary, steps, type Destination, type Pair } from "./content";
import glossary from "./glossary.json";

const metricNames: Record<string, string[]> = glossary.metrics;
const companyNames: Record<string, string[]> = glossary.companies;
// Filings name the same company several ways; the glossary keys companies by ticker.
const companyAliases: Record<string, string> = glossary.company_aliases;
export function label(map: "metric" | "company", key: string, lang: Lang) {
  const names = map === "metric" ? metricNames : companyNames;
  const id = map === "company" ? companyAliases[key] ?? key : key;
  return names[id]?.[lang === "ko" ? 0 : 1] || key;
}
export const periodLabel = (period: string, lang: Lang) => lang === "ko" ? `${period} 회계연도` : `FY${period}`;
const regulatorName = (regulator: string) => regulator === "dart" ? "DART" : "SEC";
const percent = (value: string | null) => (value === null ? "–" : value.replace("-", "−") + "%");

type Inspect = (value: Figure | Answer, e?: React.MouseEvent<HTMLElement>) => void;
type T = (ko: string, en: string) => string;

export function SourceBadge({ regulator }: { regulator: string }) {
  return <span className={"badge " + regulator}>{regulatorName(regulator)}</span>;
}

export function Home({ lang, t, go, live }: { lang: Lang; t: T; go: (d: Destination) => void; live: boolean }) {
  return (
    <div className="page home">
      <section className="hero">
        <p className="label">{t("공시 수치 조사", "Filing figure investigation")}</p>
        <h1>{t("공시 속 숫자를\n원문까지 따라갑니다", "Follow a filing figure\nback to its source")}</h1>
        <p className="lede">
          {t(
            "한국 DART와 미국 SEC 공시에서 매출액, 영업이익, 당기순이익을 묻고 비교합니다. 답에 쓰인 숫자는 모두 원문 어디에 있는지 바로 확인할 수 있습니다.",
            "Ask about revenue, operating income and net income in Korean DART and US SEC filings, then compare them. Every number in an answer opens the exact place it came from.",
          )}
        </p>
        <div className="hero-actions">
          <button className="primary" onClick={() => go({ view: "investigate", scenario: 0 })}>
            {live ? t("질문 시작하기", "Start asking") : t("녹화된 조사 보기", "Watch a recorded investigation")}
          </button>
          <button onClick={() => go({ view: "guide", anchor: "top" })}>{t("공시가 처음이라면", "New to filings? Start here")}</button>
        </div>
        {!live && (
          <p className="note">
            {t(
              "이 공개 사이트는 실제 실행을 녹화해 보여 줍니다. 새 질문은 소유자의 Mac에서 실행하는 로컬 앱에서만 받습니다.",
              "This public site replays real recorded runs. New questions run only in the local app on the owner's Mac.",
            )}
          </p>
        )}
      </section>

      <section className="block" aria-labelledby="library-title">
        <div className="section-head">
          <h2 id="library-title">{t("공시로 답할 수 있는 질문", "Questions filings can answer")}</h2>
          <p>{t("궁금한 질문을 고르면 답이 있는 곳으로 이동합니다.", "Pick a question to go where it is answered.")}</p>
        </div>
        <ul className="question-grid">
          {questionLibrary.map((item) => (
            <li key={item.question.en}>
              <button className="question-card" onClick={() => go(item.to)}>
                <span className="question-text">{pick(item.question, lang)}</span>
                <span className="question-hint">{pick(item.hint, lang)}</span>
                <span className="question-to">
                  {item.to.view === "investigate"
                    ? live ? t("조사", "Investigate") : t("녹화된 조사", "Recorded run")
                    : item.to.view === "ledger" ? t("수치 장부", "Ledger") : t("공시 가이드", "Guide")}
                  <span aria-hidden="true"> →</span>
                </span>
              </button>
            </li>
          ))}
        </ul>
      </section>

      <section className="block" aria-labelledby="how-title">
        <div className="section-head">
          <h2 id="how-title">{t("답이 만들어지는 과정", "How an answer is made")}</h2>
          <p>{t("모델은 질문만 해석하고, 숫자와 계산은 코드가 맡습니다.", "The model only reads the question. Code owns every number and calculation.")}</p>
        </div>
        <ol className="steps-row">
          {steps.map((step, i) => (
            <li key={i}>
              <span className="step-index">{String(i + 1).padStart(2, "0")}</span>
              <h3>{pick(step.title, lang)}</h3>
              <p>{pick(step.body, lang)}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="block" aria-labelledby="coverage-title">
        <div className="section-head">
          <h2 id="coverage-title">{t("검증한 범위", "Verified coverage")}</h2>
          <p>{t("회사 3곳, 회계연도 5개, 연결 기준 수치 15개입니다.", "Three companies, five fiscal years, fifteen consolidated figures.")}</p>
        </div>
        <table className="ledger-table coverage">
          <thead>
            <tr>
              <th scope="col">{t("회사", "Company")}</th>
              <th scope="col">{t("공시", "Filed with")}</th>
              <th scope="col">2022</th>
              <th scope="col">2023</th>
              <th scope="col">2024</th>
            </tr>
          </thead>
          <tbody>
            {([["삼성전자", "dart", 1, 1, 0], ["NAVER", "dart", 0, 1, 0], ["Microsoft", "sec", 0, 1, 1]] as const).map(([company, regulator, ...years]) => (
              <tr key={company}>
                <th scope="row">{label("company", company, lang)}</th>
                <td><SourceBadge regulator={regulator} /></td>
                {years.map((covered, i) => (
                  <td key={i} className="mark">
                    {covered ? <span aria-label={t("검증됨", "Verified")}>●</span> : <span aria-label={t("없음", "Not covered")} className="muted">–</span>}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <p className="note">
          {t(
            "매출액, 영업이익, 당기순이익만 다룹니다. 마이크로소프트의 회계연도는 6월에 끝납니다.",
            "Revenue, operating income and net income only. Microsoft's fiscal year ends in June.",
          )}
        </p>
      </section>

      <Family lang={lang} t={t} />
    </div>
  );
}

export function Family({ lang, t }: { lang: Lang; t: T }) {
  return (
    <section className="block family" aria-labelledby="family-title">
      <div className="section-head">
        <h2 id="family-title">{pick(family.title, lang)}</h2>
        <p>{t("같은 검증 원칙을 쓰는 두 앱이 각자 다른 질문을 맡습니다.", "Two apps share one evidence discipline and answer different questions.")}</p>
      </div>
      <div className="family-grid">
        <div className="family-card digest">
          <p className="family-mark-label">[F] Filing Digest</p>
          <p>{pick(family.digest.role, lang)}</p>
          <a href={family.digest.url}>{pick(family.digest.link, lang)} ↗</a>
        </div>
        <div className="family-card agent">
          <p className="family-mark-label">[F] Filing Agent</p>
          <p>{pick(family.agent.role, lang)}</p>
          <span className="muted">{t("지금 보고 있는 앱", "You are here")}</span>
        </div>
      </div>
    </section>
  );
}

export function Guide({ lang, t }: { lang: Lang; t: T }) {
  const g = guide;
  return (
    <article className="page guide">
      <header className="page-head">
        <p className="label">{t("처음 읽는 분을 위한", "For first-time readers")}</p>
        <h1>{pick(g.title, lang)}</h1>
        <p className="lede">{pick(g.lede, lang)}</p>
        <nav className="toc" aria-label={t("가이드 목차", "Guide contents")}>
          {[["what", g.what.title], ["kinds", g.kinds.title], ["report-map", g.map.title], ["numbers", g.numbers.title], ["scope", g.scope.title]].map(([id, title]) => (
            <a key={id as string} href={"#" + id} onClick={(e) => { e.preventDefault(); document.getElementById(id as string)?.scrollIntoView({ block: "start" }); }}>
              {pick(title as Pair, lang)}
            </a>
          ))}
        </nav>
      </header>

      <section className="block" id="what">
        <h2>{pick(g.what.title, lang)}</h2>
        <p className="prose">{pick(g.what.body, lang)}</p>
        <ul className="where-grid">
          {g.where.map((w) => (
            <li key={w.name}>
              <a href={w.url} target="_blank" rel="noreferrer"><strong>{w.name}</strong> ↗</a>
              <span className="muted">{pick(w.who, lang)}</span>
              <p>{pick(w.what, lang)}</p>
            </li>
          ))}
        </ul>
      </section>

      <section className="block" id="kinds">
        <h2>{pick(g.kinds.title, lang)}</h2>
        <div className="table-scroll">
          <table className="ledger-table stack-table">
            <thead><tr>{g.kinds.head.map((h) => <th scope="col" key={h.en}>{pick(h, lang)}</th>)}</tr></thead>
            <tbody>
              {g.kinds.rows.map((row) => (
                <tr key={row[0].en}>
                  <th scope="row">{pick(row[0], lang)}</th>
                  {row.slice(1).map((cell, i) => <td key={i} data-label={pick(g.kinds.head[i + 1], lang)}>{pick(cell, lang)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="block" id="report-map">
        <h2>{pick(g.map.title, lang)}</h2>
        <p className="prose">{pick(g.map.lede, lang)}</p>
        <div className="table-scroll">
          <table className="ledger-table stack-table">
            <thead><tr>{g.map.head.map((h) => <th scope="col" key={h.en}>{pick(h, lang)}</th>)}</tr></thead>
            <tbody>
              {g.map.rows.map(([q, kr, us]) => (
                <tr key={q.en}>
                  <th scope="row">{pick(q, lang)}</th>
                  <td lang="ko" data-label={pick(g.map.head[1], lang)}>{pick(kr, lang)}</td>
                  <td lang="en" data-label={g.map.head[2].en}>{us}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="note">{pick(g.map.note, lang)}</p>
      </section>

      <section className="block" id="numbers">
        <h2>{pick(g.numbers.title, lang)}</h2>
        <dl className="terms">
          {g.numbers.items.map((item) => (
            <div key={item.term.en}><dt>{pick(item.term, lang)}</dt><dd>{pick(item.body, lang)}</dd></div>
          ))}
        </dl>
        <h3 className="subhead">{pick(g.metrics.title, lang)}</h3>
        <dl className="terms">
          {g.metrics.items.map((item) => (
            <div key={item.term.en}><dt>{pick(item.term, lang)}</dt><dd>{pick(item.body, lang)}</dd></div>
          ))}
        </dl>
      </section>

      <section className="block" id="scope">
        <h2>{pick(g.scope.title, lang)}</h2>
        <div className="scope-grid">
          <div><h3>{pick(g.scope.canTitle, lang)}</h3><ul>{g.scope.can[lang].map((x) => <li key={x}>{x}</li>)}</ul></div>
          <div><h3>{pick(g.scope.cannotTitle, lang)}</h3><ul>{g.scope.cannot[lang].map((x) => <li key={x}>{x}</li>)}</ul></div>
        </div>
        <p className="note">{t("이 앱의 내용은 투자 권유가 아닙니다.", "Nothing in this app is investment advice.")}</p>
      </section>
    </article>
  );
}

type LedgerData = { snapshot_id: string; figures: Figure[] };
const companies = ["삼성전자", "NAVER", "Microsoft"];
const metrics = ["revenue", "operating_income", "net_income"];

export function useLedger() {
  const [data, setData] = useState<LedgerData | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    fetch("./ledger.json", { signal: controller.signal })
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then(setData)
      .catch((e) => { if (e.name !== "AbortError") setFailed(true); });
    return () => controller.abort();
  }, []);
  return { data, failed };
}

function Value({ f, lang, inspect, selected }: { f: Figure; lang: Lang; inspect: Inspect; selected: string | null }) {
  return (
    <button
      className={"value-button" + (selected === f.id ? " selected" : "")}
      onClick={(e) => inspect(f, e)}
      aria-label={`${label("company", f.company, lang)} ${periodLabel(f.period, lang)} ${label("metric", f.metric, lang)} ${compact(f.value, f.currency, lang)}, ${lang === "ko" ? "원문 근거 보기" : "inspect source"}`}
    >
      {compact(f.value, f.currency, lang)}
    </button>
  );
}

export function Ledger({ lang, t, inspect, selected, data, failed, anchor }: {
  lang: Lang; t: T; inspect: Inspect; selected: string | null;
  data: LedgerData | null; failed: boolean; anchor: string | null;
}) {
  useEffect(() => {
    if (data && anchor) document.getElementById(anchor)?.scrollIntoView({ block: "start" });
  }, [data, anchor]);
  if (failed) return <div className="page"><p role="alert">{t("수치 장부를 불러오지 못했습니다.", "The ledger could not be loaded.")}</p></div>;
  if (!data) return <div className="page"><p role="status">{t("수치 장부를 불러오는 중입니다.", "Loading the ledger.")}</p></div>;
  const get = (company: string, period: string, metric: string) =>
    data.figures.find((f) => f.company === company && f.period === period && f.metric === metric)!;
  const v = (f: Figure) => <Value f={f} lang={lang} inspect={inspect} selected={selected} />;
  const name = (c: string) => label("company", c, lang);

  const s22r = get("삼성전자", "2022", "revenue"), s22o = get("삼성전자", "2022", "operating_income");
  const s23r = get("삼성전자", "2023", "revenue"), s23o = get("삼성전자", "2023", "operating_income"), s23n = get("삼성전자", "2023", "net_income");
  const m23r = get("Microsoft", "2023", "revenue"), m24r = get("Microsoft", "2024", "revenue");
  const m23o = get("Microsoft", "2023", "operating_income"), m24o = get("Microsoft", "2024", "operating_income");
  const n23r = get("NAVER", "2023", "revenue"), n23o = get("NAVER", "2023", "operating_income");
  const margin23 = ratio(s23o.value, s23r.value), margin22 = ratio(s22o.value, s22r.value);
  const growthRevenue = change(m24r.value, m23r.value).percent!, growthOperating = change(m24o.value, m23o.value).percent!;
  const compareRows = [[n23o, n23r], [m23o, m23r], [s23o, s23r]]
    .map(([o, r]) => ({ o, r, m: ratio(o.value, r.value)! }))
    .sort((a, b) => Number(b.m) - Number(a.m));

  return (
    <div className="page ledger">
      <header className="page-head">
        <p className="label">{t("검증한 수치 15개", "Fifteen verified figures")}</p>
        <h1>{t("수치 장부", "Figure ledger")}</h1>
        <p className="lede">
          {t(
            "검증한 수치를 회사별로 펼쳤습니다. 이익률과 증감률은 이 수치로 계산하며, 금액을 누르면 원문 근거가 열립니다.",
            "Every verified figure, by company. Margins and changes are calculated from these values, and each amount opens its source.",
          )}
        </p>
      </header>

      <section className="block" aria-labelledby="answers-title">
        <h2 id="answers-title">{t("수치로 답하는 질문", "Questions these figures answer")}</h2>
        <div className="insights">
          <article className="insight" id="margin">
            <h3>{t("매출 100원당 얼마를 남기나요?", "How much of each sale becomes profit?")}</h3>
            <p className="insight-figure">{percent(margin23)}</p>
            <p>
              {t(
                `${name("삼성전자")}의 2023년 영업이익률입니다. 매출 100원당 영업이익이 ${margin23}원으로, 2022년 ${margin22}원보다 줄었습니다.`,
                `Samsung's FY2023 operating margin: ${margin23} of every 100 in revenue became operating income, down from ${margin22} in FY2022.`,
              )}
            </p>
            <p className="calc">
              {t("영업이익", "Operating income")} {v(s23o)} ÷ {t("매출액", "revenue")} {v(s23r)}
            </p>
          </article>

          <article className="insight" id="net-vs-operating">
            <h3>{t("순이익이 영업이익보다 클 수 있나요?", "Can net income exceed operating income?")}</h3>
            <p className="insight-figure">{compact(s23n.value, s23n.currency, lang)} &gt; {compact(s23o.value, s23o.currency, lang)}</p>
            <p>
              {t(
                "있습니다. 삼성전자의 2023년 당기순이익은 영업이익보다 큽니다. 순이익에는 이자, 투자 같은 영업 외 손익과 법인세가 반영되기 때문입니다. 어떤 항목이 차이를 만들었는지는 사업보고서의 연결재무제표 주석에 있으며, 이 장부의 범위 밖입니다.",
                "Yes. Samsung's FY2023 net income was larger than its operating income, because net income also includes non-operating items such as interest and investments, and income tax. Which items made the difference is in the notes to the annual report, outside this ledger.",
              )}
            </p>
            <p className="calc">
              {t("당기순이익", "Net income")} {v(s23n)} &gt; {t("영업이익", "operating income")} {v(s23o)}
            </p>
          </article>

          <article className="insight" id="compare">
            <h3>{t("규모가 다른 회사는 어떻게 비교하나요?", "How do you compare companies of different sizes?")}</h3>
            <ol className="bars" aria-label={t("2023 회계연도 영업이익률", "FY2023 operating margin")}>
              {compareRows.map(({ o, m }) => (
                <li key={o.company}>
                  <span className="bar-name">{name(o.company)}</span>
                  <span className="bar-track" aria-hidden="true"><span className="bar-fill" style={{ width: `${Math.min(100, Number(m) * 2)}%` }} /></span>
                  <span className="bar-value">{percent(m)}</span>
                </li>
              ))}
            </ol>
            <p>
              {t(
                "원화와 달러 금액을 바로 비교하지 않고 영업이익률로 비교합니다. 2023 회계연도 기준입니다. 마이크로소프트의 회계연도는 6월에 끝나므로 기간이 6개월 어긋납니다.",
                "Compare operating margins instead of won against dollars. All are FY2023; Microsoft's fiscal year ends in June, so its period is offset by six months.",
              )}
            </p>
            <p className="calc">
              {compareRows.map(({ o, r }) => (
                <span key={o.company} className="calc-line">{name(o.company)} {v(o)} ÷ {v(r)}</span>
              ))}
            </p>
          </article>

          <article className="insight" id="growth">
            <h3>{t("마이크로소프트는 성장했나요?", "Did Microsoft grow?")}</h3>
            <p className="insight-figure">{signedPercent(growthRevenue)}</p>
            <p>
              {t(
                `2024 회계연도 매출액이 전년보다 ${growthRevenue}% 늘었고, 영업이익은 ${growthOperating}% 늘었습니다. 영업이익이 매출보다 빠르게 늘었다는 뜻입니다.`,
                `FY2024 revenue rose ${growthRevenue}% from FY2023, and operating income rose ${growthOperating}%. Operating income grew faster than revenue.`,
              )}
            </p>
            <p className="calc">
              <span className="nowrap">({v(m24r)} − {v(m23r)})</span>{" "}
              <span className="nowrap">÷ {v(m23r)}</span>
            </p>
          </article>
        </div>
      </section>

      {companies.map((company) => {
        const years = [...new Set(data.figures.filter((f) => f.company === company).map((f) => f.period))].sort();
        const two = years.length === 2;
        return (
          <section className="block" key={company} aria-labelledby={"ledger-" + company}>
            <div className="company-head">
              <h2 id={"ledger-" + company}>{name(company)}</h2>
              <SourceBadge regulator={get(company, years[0], "revenue").source.regulator} />
              <span className="muted">{[...new Set(years.map((y) => get(company, y, "revenue").source.filing_title))].join(" · ")}</span>
            </div>
            <div className="table-scroll" tabIndex={0} role="region" aria-label={`${name(company)} ${t("수치표", "figure table")}`}>
              <table className="ledger-table figures-table">
                <thead>
                  <tr>
                    <th scope="col">{t("지표", "Metric")}</th>
                    {years.map((y) => <th scope="col" key={y} className="num">{periodLabel(y, lang)}</th>)}
                    {two && <th scope="col" className="num">{t("증감", "Change")}</th>}
                  </tr>
                </thead>
                <tbody>
                  {metrics.map((metric) => (
                    <tr key={metric}>
                      <th scope="row">{label("metric", metric, lang)}</th>
                      {years.map((y) => <td key={y} className="num">{v(get(company, y, metric))}</td>)}
                      {two && <td className="num derived">{signedPercent(change(get(company, years[1], metric).value, get(company, years[0], metric).value).percent!)}</td>}
                    </tr>
                  ))}
                  {[["operating_income", t("영업이익률", "Operating margin")], ["net_income", t("순이익률", "Net margin")]].map(([metric, title]) => (
                    <tr key={metric} className="derived-row">
                      <th scope="row">{title}<span className="derived-tag">{t("계산", "calc")}</span></th>
                      {years.map((y) => <td key={y} className="num derived">{percent(ratio(get(company, y, metric).value, get(company, y, "revenue").value))}</td>)}
                      {two && <td />}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        );
      })}
      <p className="note">
        {t(
          "계산 값은 위 금액으로 구했습니다. 이익률은 소수 첫째 자리, 증감률은 둘째 자리에서 반올림합니다.",
          "Calculated values use the amounts above. Margins round to one decimal place, changes to two.",
        )}
      </p>
    </div>
  );
}

function highlight(text: string, needle: string) {
  const i = text.indexOf(needle);
  if (i < 0) return text;
  return <>{text.slice(0, i)}<mark>{needle}</mark>{text.slice(i + needle.length)}</>;
}

export function EvidenceBody({ evidence, lang, t }: { evidence: Figure | Answer; lang: Lang; t: T }) {
  if (!("id" in evidence)) {
    return (
      <>
        <p className="label">{t("확인한 범위", "Checked scope")}</p>
        <p className="evidence-answer">{evidence[lang === "ko" ? "answer_ko" : "answer_en"]}</p>
        <p className="limitation">
          {t(
            "검증된 지표 목록을 조회했습니다. 공시 전체를 검색했다는 뜻은 아닙니다.",
            "This lookup checked the verified metric catalog, not the full filings.",
          )}
        </p>
        <ul className="trail">
          {evidence.searched.map((s, i) => (
            <li key={i}>
              <strong>{label("company", s.company, lang)}</strong> · {s.filing_title}
              <span className="muted">{s.section}</span>
            </li>
          ))}
        </ul>
      </>
    );
  }
  const f = evidence;
  const original = f.source.regulator === "dart" ? "ko" : "en";
  return (
    <>
      <p className="label">{t("원문 발췌 · 번역하지 않음", "Original excerpt · not translated")}</p>
      <div className="excerpt" lang={original}>
        {f.source.excerpt_cells ? (
          <table>
            <tbody>
              <tr>
                {f.source.excerpt_cells.map((cell, i) => (
                  <td key={i} className={i === 0 ? "row-label" : cell === f.original_value ? "hit" : undefined}>
                    {cell === f.original_value ? <mark>{cell}</mark> : cell}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        ) : (
          <p>{highlight(f.source.excerpt || f.source_label, f.original_value)}</p>
        )}
        <p className="excerpt-unit">{t("단위", "Unit")}: {f.original_unit}</p>
      </div>

      <dl className="source-facts">
        <div><dt>{t("회사", "Company")}</dt><dd>{label("company", f.company, lang)}</dd></div>
        <div><dt>{t("공시", "Filing")}</dt><dd>{f.source.filing_title} <SourceBadge regulator={f.source.regulator} /></dd></div>
        <div><dt>{t("위치", "Location")}</dt><dd>{f.source.section || "Inline XBRL"}</dd></div>
        <div><dt>{t("기간", "Period")}</dt><dd className="num">{f.period_start} ~ {f.period_end}</dd></div>
        <div><dt>{t("기준", "Basis")}</dt><dd>{t("연결", "Consolidated")}</dd></div>
      </dl>

      <h3 className="subhead">{t("원문에서 화면까지", "From filing to screen")}</h3>
      <ol className="reconcile">
        <li><span>{t("원문", "Filing")}</span><strong className="num">{f.original_value} ({f.original_unit})</strong></li>
        <li><span>{t("정확한 값", "Exact value")}</span><strong className="num">{exact(f.value)} {f.currency === "KRW" ? t("원", "KRW") : t("달러", "USD")}</strong></li>
        {lang === "ko" && f.currency === "KRW" && <li><span>{t("읽는 법", "Read as")}</span><strong className="num">{koreanUnits(f.value)}</strong></li>}
        <li><span>{t("화면 표시", "Displayed")}</span><strong className="num">{compact(f.value, f.currency, lang)}</strong></li>
      </ol>

      <a className="source-link" href={f.source.url} target="_blank" rel="noreferrer">
        {f.source.regulator === "dart" ? t("DART에서 원문 공시 열기", "Open the filing on DART") : t("SEC에서 원문 공시 열기", "Open the filing on SEC")} ↗
      </a>
      <p className="note">
        {f.source.regulator === "sec"
          ? t("SEC는 자동화된 접근을 제한할 수 있습니다. 링크는 새 탭에서 열립니다. ", "SEC may restrict automated access. The link opens in a new tab. ")
          : ""}
        {t(
          "고정된 과거 공시입니다. 이후 정정 공시는 전부 검토하지 않았습니다.",
          "This is a pinned historical filing. Later amendments have not been exhaustively reviewed.",
        )}
      </p>
    </>
  );
}
