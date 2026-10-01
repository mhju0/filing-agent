// Product copy that is not tied to a single control. Korean uses 합니다체;
// full sentences end with a period, labels and headings do not.
import type { Lang } from "./format";

export type Pair = { ko: string; en: string };
// A word joiner keeps form codes such as 8-K and 10-Q from breaking at the hyphen.
export const pick = (pair: Pair, lang: Lang) => pair[lang].replace(/(\d)-([A-Z])/g, "$1-\u2060$2");

export type View = "home" | "investigate" | "ledger" | "guide";

export const scenarios: { title: Pair; notice: Pair; turns: Pair[] }[] = [
  {
    title: { ko: "연간 비교", en: "Annual comparison" },
    notice: {
      ko: "두 번째 질문은 회사와 지표를 다시 말하지 않습니다. 앞 질문의 문맥을 이어받아 같은 회사의 두 해를 비교합니다.",
      en: "The second question never repeats the company or metric. The context carries over, so it compares two years of the same company.",
    },
    turns: [
      { ko: "검증된 수치 하나와 그 원문 발췌를 확인합니다.", en: "One verified figure and the excerpt it came from." },
      { ko: "앞 질문의 회사와 지표를 그대로 쓰고, 두 수치로 증감률을 계산합니다.", en: "The company and metric carry over, and code calculates the change from the two figures." },
    ],
  },
  {
    title: { ko: "회사 전환", en: "Company switch" },
    notice: {
      ko: "“네이버는?”만으로 지표와 연도는 그대로 두고 회사만 바꿉니다.",
      en: "“What about NAVER?” keeps the metric and year and changes only the company.",
    },
    turns: [
      { ko: "삼성전자의 2023년 매출액으로 문맥을 만듭니다.", en: "Samsung's FY2023 revenue sets the context." },
      { ko: "회사만 바꾸고 지표와 연도는 유지합니다. 다른 회사의 수치를 빌려 쓰지 않습니다.", en: "Only the company changes. No figure is borrowed from another company." },
    ],
  },
  {
    title: { ko: "근거 부족", en: "Missing evidence" },
    notice: {
      ko: "검증 모음에 없는 지표를 물으면 숫자를 만들지 않고, 무엇을 확인했는지 보여 줍니다.",
      en: "When a metric is not in the verified collection, no number is invented. The answer shows what was checked.",
    },
    turns: [
      { ko: "연구개발비는 검증 모음에 없으므로 수치를 비워 두고 확인한 범위를 표시합니다.", en: "R&D is not in the verified collection, so the figure stays empty and the checked scope is shown." },
    ],
  },
];

export type Destination =
  | { view: "investigate"; scenario: number }
  | { view: "ledger"; anchor: string }
  | { view: "guide"; anchor: string };

export const questionLibrary: { question: Pair; hint: Pair; to: Destination }[] = [
  {
    question: { ko: "작년보다 매출이 늘었나요?", en: "Did revenue grow from last year?" },
    hint: { ko: "삼성전자 2023년 매출액을 묻고, 이어서 2022년과 비교합니다.", en: "Ask for Samsung's FY2023 revenue, then compare it with FY2022." },
    to: { view: "investigate", scenario: 0 },
  },
  {
    question: { ko: "매출 100원당 얼마를 남기나요?", en: "How much of each sale becomes profit?" },
    hint: { ko: "영업이익률로 본업의 수익성을 봅니다.", en: "Operating margin shows how profitable the core business is." },
    to: { view: "ledger", anchor: "margin" },
  },
  {
    question: { ko: "순이익이 영업이익보다 클 수 있나요?", en: "Can net income exceed operating income?" },
    hint: { ko: "삼성전자 2023년에 실제로 그랬습니다.", en: "It happened at Samsung in FY2023." },
    to: { view: "ledger", anchor: "net-vs-operating" },
  },
  {
    question: { ko: "규모가 다른 회사는 어떻게 비교하나요?", en: "How do you compare companies of different sizes?" },
    hint: { ko: "원화와 달러를 바로 비교하지 않고 이익률로 비교합니다.", en: "Compare margins, not won against dollars." },
    to: { view: "ledger", anchor: "compare" },
  },
  {
    question: { ko: "네이버는요?", en: "What about NAVER?" },
    hint: { ko: "한 마디 후속 질문으로 회사만 바꿉니다.", en: "A two-word follow-up switches only the company." },
    to: { view: "investigate", scenario: 1 },
  },
  {
    question: { ko: "없는 수치를 물으면 어떻게 되나요?", en: "What happens when the figure isn't there?" },
    hint: { ko: "숫자를 지어내지 않고 확인한 범위를 보여 줍니다.", en: "No number is invented; the checked scope is shown." },
    to: { view: "investigate", scenario: 2 },
  },
  {
    question: { ko: "배당과 최대주주는 어디서 보나요?", en: "Where do I find dividends and major shareholders?" },
    hint: { ko: "사업보고서에서 질문별로 볼 곳을 안내합니다.", en: "A map from questions to annual report sections." },
    to: { view: "guide", anchor: "report-map" },
  },
  {
    question: { ko: "258,935,494(백만원)은 얼마인가요?", en: "What does 258,935,494 (KRW millions) mean?" },
    hint: { ko: "원문 표의 단위를 읽는 법입니다.", en: "How to read the units in a filing table." },
    to: { view: "guide", anchor: "numbers" },
  },
];

export const steps: { title: Pair; body: Pair }[] = [
  {
    title: { ko: "질문 해석", en: "Read the question" },
    body: {
      ko: "로컬 모델은 회사, 지표, 회계연도만 해석합니다. 공시 원문이나 금액은 받지 않습니다.",
      en: "A local model reads only the company, metric and fiscal year. It never sees filing text or amounts.",
    },
  },
  {
    title: { ko: "근거 선택과 계산", en: "Select evidence and calculate" },
    body: {
      ko: "코드가 검증된 수치만 고르고 증감률을 계산합니다. 근거가 없으면 숫자를 비워 둡니다.",
      en: "Code selects verified figures and calculates changes. Without evidence, the figure stays empty.",
    },
  },
  {
    title: { ko: "원문 확인", en: "Check the source" },
    body: {
      ko: "모든 숫자에서 원문 발췌, 원래 단위, 공시 링크를 바로 엽니다.",
      en: "Every number opens its original excerpt, original unit and filing link.",
    },
  },
];

export const guide = {
  title: { ko: "공시 가이드", en: "Filing guide" },
  lede: {
    ko: "공시가 무엇이고 어디서 보며, 사업보고서에서 무엇을 찾을 수 있는지 정리했습니다.",
    en: "What a filing is, where to find one, and what an annual report can answer.",
  },
  what: {
    title: { ko: "공시란 무엇인가요", en: "What is a filing?" },
    body: {
      ko: "공시는 상장회사가 투자자에게 알려야 하는 정보를 법에 따라 공개하는 것입니다. 실적, 사업 내용, 자금 조달, 중요한 결정이 모두 공시로 나옵니다. 원문은 누구나 무료로 볼 수 있습니다.",
      en: "A filing (공시, gongsi) is information a listed company must disclose by law. Results, business descriptions, fundraising and major decisions all appear as filings, and anyone can read the originals for free.",
    },
  },
  where: [
    {
      name: "DART",
      url: "https://dart.fss.or.kr",
      who: { ko: "금융감독원 전자공시시스템", en: "Financial Supervisory Service, Korea" },
      what: { ko: "사업보고서를 비롯해 금융감독원에 제출한 공시를 모두 볼 수 있습니다.", en: "Every filing submitted to the regulator, including annual reports." },
    },
    {
      name: "KIND",
      url: "https://kind.krx.co.kr",
      who: { ko: "한국거래소 기업공시채널", en: "Korea Exchange disclosure channel" },
      what: { ko: "공정공시처럼 거래소에만 내는 공시와 투자 주의 같은 시장 조치를 봅니다.", en: "Exchange-only disclosures such as fair disclosures, plus market actions like investment warnings." },
    },
    {
      name: "EDGAR",
      url: "https://www.sec.gov/edgar/search/",
      who: { ko: "미국 증권거래위원회(SEC)", en: "US Securities and Exchange Commission" },
      what: { ko: "마이크로소프트 같은 미국 상장회사의 10-K, 10-Q, 8-K를 봅니다.", en: "10-K, 10-Q and 8-K filings from US-listed companies such as Microsoft." },
    },
  ],
  kinds: {
    title: { ko: "공시의 종류", en: "Kinds of filings" },
    head: [
      { ko: "종류", en: "Kind" },
      { ko: "무엇을 알리나요", en: "What it tells you" },
      { ko: "대표 문서", en: "Typical document" },
      { ko: "미국에서는", en: "US counterpart" },
    ],
    rows: [
      [
        { ko: "정기공시", en: "Periodic" },
        { ko: "정해진 시기마다 사업과 재무 상태 전반", en: "The business and finances, on a fixed schedule" },
        { ko: "사업보고서, 반기보고서, 분기보고서", en: "Annual, half-year and quarterly reports" },
        { ko: "10-K, 10-Q", en: "10-K, 10-Q" },
      ],
      [
        { ko: "주요사항보고", en: "Material events" },
        { ko: "증자, 합병, 영업 양수도 같은 중요한 결정", en: "Major decisions such as share issues, mergers and asset transfers" },
        { ko: "주요사항보고서", en: "Material event report" },
        { ko: "8-K", en: "8-K" },
      ],
      [
        { ko: "발행공시", en: "Securities issuance" },
        { ko: "주식이나 채권을 새로 발행하는 조건", en: "Terms of new shares or bonds" },
        { ko: "증권신고서, 투자설명서", en: "Registration statement, prospectus" },
        { ko: "S-1, S-3", en: "S-1, S-3" },
      ],
      [
        { ko: "지분공시", en: "Ownership" },
        { ko: "5% 이상 보유와 그 변동", en: "Holdings of 5% or more and their changes" },
        { ko: "주식등의대량보유상황보고서", en: "Large shareholding report" },
        { ko: "Schedule 13D, 13G", en: "Schedule 13D, 13G" },
      ],
      [
        { ko: "거래소 공시", en: "Exchange disclosures" },
        { ko: "잠정 실적, 실적 전망 같은 거래소 규정 공시", en: "Preliminary results and guidance under exchange rules" },
        { ko: "공정공시 (KIND)", en: "Fair disclosure (KIND)" },
        { ko: "8-K (실적 발표)", en: "8-K (earnings release)" },
      ],
    ],
  },
  map: {
    title: { ko: "사업보고서에서 어디를 보나요", en: "Where to look in an annual report" },
    lede: {
      ko: "사업보고서는 목차가 정해진 양식입니다. 질문에 맞는 장을 바로 열면 됩니다.",
      en: "Korean annual reports (사업보고서) follow a fixed outline. Open the chapter that matches your question.",
    },
    rows: [
      [{ ko: "무슨 사업을 하나요?", en: "What does the company do?" }, { ko: "II. 사업의 내용", en: "II. 사업의 내용 (Business)" }, "Item 1"],
      [{ ko: "얼마나 벌었나요?", en: "How much did it earn?" }, { ko: "III. 재무에 관한 사항 › 1. 요약재무정보", en: "III › 1. 요약재무정보 (Summary financials)" }, "Item 8"],
      [{ ko: "숫자 뒤의 사정은요?", en: "What is behind a number?" }, { ko: "III › 3. 연결재무제표 주석", en: "III › 3. 연결재무제표 주석 (Notes)" }, "Item 8 (Notes)"],
      [{ ko: "경영진은 실적을 어떻게 설명하나요?", en: "How does management explain results?" }, { ko: "IV. 이사의 경영진단 및 분석의견", en: "IV. 이사의 경영진단 및 분석의견 (MD&A)" }, "Item 7"],
      [{ ko: "감사인 의견은요?", en: "What did the auditor say?" }, { ko: "V. 회계감사인의 감사의견 등", en: "V. 회계감사인의 감사의견 등 (Audit opinion)" }, "Item 8, 9A"],
      [{ ko: "배당은 얼마였나요?", en: "How much was the dividend?" }, { ko: "III › 6. 배당에 관한 사항", en: "III › 6. 배당에 관한 사항 (Dividends)" }, "Item 5"],
      [{ ko: "최대주주는 누구인가요?", en: "Who is the largest shareholder?" }, { ko: "VII. 주주에 관한 사항", en: "VII. 주주에 관한 사항 (Shareholders)" }, "Item 12"],
      [{ ko: "직원 수와 보수는요?", en: "How many employees, and their pay?" }, { ko: "VIII. 임원 및 직원 등에 관한 사항", en: "VIII. 임원 및 직원 등에 관한 사항 (Officers and employees)" }, "Item 1, 11"],
    ] as [Pair, Pair, string][],
    head: [
      { ko: "질문", en: "Question" },
      { ko: "사업보고서", en: "Korean annual report" },
      { ko: "10-K", en: "10-K" },
    ],
    note: {
      ko: "목차는 삼성전자 2025년 1분기 보고서에서 확인한 표준 양식입니다. 회사와 연도에 따라 하위 번호가 조금 다를 수 있습니다.",
      en: "Outline checked against Samsung's Q1 2025 report. Sub-section numbers can vary slightly by company and year.",
    },
  },
  numbers: {
    title: { ko: "숫자를 읽는 법", en: "Reading the numbers" },
    items: [
      {
        term: { ko: "단위", en: "Units" },
        body: {
          ko: "원문 표는 대개 백만원 단위입니다. 258,935,494(백만원)은 258조 9,354억 9,400만 원입니다.",
          en: "Korean filing tables are usually in KRW millions. 258,935,494 (KRW millions) is about 258.9 trillion won.",
        },
      },
      {
        term: { ko: "연결과 별도", en: "Consolidated vs separate" },
        body: {
          ko: "연결은 자회사를 포함한 그룹 전체, 별도는 회사 하나의 수치입니다. 이 앱은 연결 기준만 다룹니다.",
          en: "Consolidated covers the whole group including subsidiaries; separate covers the parent alone. This app uses consolidated figures only.",
        },
      },
      {
        term: { ko: "회계연도", en: "Fiscal year" },
        body: {
          ko: "삼성전자와 네이버는 12월에 결산합니다. 마이크로소프트는 6월에 결산하므로 2024 회계연도(FY2024)는 2023년 7월부터 2024년 6월까지입니다.",
          en: "Samsung and NAVER close their books in December. Microsoft closes in June, so FY2024 runs from July 2023 to June 2024.",
        },
      },
      {
        term: { ko: "같은 지표, 다른 이름", en: "Same metric, different labels" },
        body: {
          ko: "삼성전자와 네이버의 손익계산서는 매출액을 ‘영업수익’으로 적습니다. 마이크로소프트는 ‘Total revenue’입니다.",
          en: "Samsung and NAVER label revenue as 영업수익 (operating revenue). Microsoft uses ‘Total revenue’.",
        },
      },
    ],
  },
  metrics: {
    title: { ko: "세 가지 지표", en: "The three metrics" },
    items: [
      {
        term: { ko: "매출액", en: "Revenue" },
        body: { ko: "제품과 서비스를 팔아 들어온 금액입니다.", en: "Money earned from selling products and services." },
      },
      {
        term: { ko: "영업이익", en: "Operating income" },
        body: { ko: "매출액에서 매출원가와 판매비·관리비를 뺀 본업의 이익입니다.", en: "Revenue minus cost of sales and operating expenses: the profit from the core business." },
      },
      {
        term: { ko: "당기순이익", en: "Net income" },
        body: { ko: "영업이익에 이자, 투자 같은 영업 외 손익과 법인세를 반영한 최종 이익입니다.", en: "Operating income after non-operating items such as interest and investments, and after income tax." },
      },
      {
        term: { ko: "이익률", en: "Margin" },
        body: { ko: "이익을 매출액으로 나눈 비율입니다. 통화와 규모가 달라도 비교할 수 있습니다.", en: "Profit divided by revenue. It compares companies across currencies and sizes." },
      },
    ],
  },
  scope: {
    title: { ko: "이 앱이 하는 일", en: "What this app does" },
    can: {
      ko: ["검증한 수치 15개 조회와 연도·회사 비교", "증감률과 이익률 계산, 계산에 쓴 수치 공개", "원문 발췌, 원래 단위, 공시 링크 확인"],
      en: ["Look up and compare 15 verified figures across years and companies", "Calculate changes and margins, showing the inputs", "Show the original excerpt, unit and filing link"],
    },
    cannot: {
      ko: ["공시 전체 검색이나 새 공시 수집", "주가, 전망, 투자 조언", "실적이 왜 바뀌었는지에 대한 설명"],
      en: ["Search entire filings or fetch new ones", "Share prices, forecasts or investment advice", "Explanations of why results changed"],
    },
    canTitle: { ko: "할 수 있는 일", en: "Does" },
    cannotTitle: { ko: "하지 않는 일", en: "Does not" },
  },
};

export const family = {
  title: { ko: "Filing Digest와 함께", en: "Works with Filing Digest" },
  digest: {
    name: "Filing Digest",
    role: { ko: "회사별 최신 공시를 요약하고, 문장마다 원문 인용을 붙여 읽는 iOS 앱입니다.", en: "An iOS reader that summarizes each company's latest filing and cites the source for every sentence." },
    link: { ko: "Filing Digest 열기", en: "Open Filing Digest" },
    url: "https://mhju0.github.io/filing-digest/",
  },
  agent: {
    name: "Filing Agent",
    role: { ko: "숫자 하나를 여러 해와 회사에 걸쳐 묻고, 원문으로 확인하는 조사 도구입니다.", en: "An investigation tool for following one number across years and companies, back to the source." },
  },
};
