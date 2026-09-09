import {setup, pair, language} from './common.js';

let recording, failed = false, scenario = 0, turn = 0, screen = 'local', selectedFigure = 0;
const content = document.querySelector('#agent-content');
const dialog = document.querySelector('#source-dialog');
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[c]));
const names = () => [pair('연도 비교', 'Annual comparison'), pair('회사 전환', 'Company switch'), pair('근거 부족', 'Missing evidence')];

function source(f) {
  return `<p class="eyebrow">${pair('공시 원문 근거', 'Original filing evidence')}</p>
    <h3>${esc(f.source.filing_title)}</h3><p>${esc(f.source.regulator.toUpperCase())} · ${esc(f.source.filing_identity)}<br>${esc(f.source.section)}</p>
    <p>${pair('원문 언어: 한국어 · 단위: ', 'Original language: Korean · Unit: ')}${pair(f.original_unit, f.original_unit === '백만원' ? 'KRW million' : 'KRW')}</p>
    <table class="source-table"><thead><tr><th>${pair('원문 항목', 'Original row')}</th><th>${esc(f.period)}</th></tr></thead><tbody><tr><td>${esc(f.source_label)}</td><td>${esc(f.original_value)}</td></tr></tbody></table>
    <p>${pair('표시 금액', 'Displayed amount')}: ${Number(f.value).toLocaleString(language === 'ko' ? 'ko-KR' : 'en-US')} ${esc(f.currency)}</p>
    <a class="source-link" href="${esc(f.source.url)}" target="_blank" rel="noopener">${pair('DART에서 해당 공시 열기', 'Open this filing on DART')}</a>`;
}

function selectScenario(index) {
  scenario = index; turn = index === 1 ? 1 : 0; selectedFigure = 0; screen = 'replay'; draw();
}

function entry() {
  return `<div class="local-start"><div class="entry-copy"><p class="eyebrow">${pair('공시를 살펴보는 개인 조사 공간', 'A personal workspace for filing research')}</p>
    <h1>${pair('질문을 이어 가며<br>근거를 확인합니다', 'Follow the question<br>Check the evidence')}</h1>
    <p>${pair('회사와 회계연도를 정해 질문해 보세요. 수치를 비교하고, 답변에 쓰인 공시 원문을 바로 확인할 수 있습니다.', 'Choose a company and fiscal year. Compare reported figures and inspect the original filing behind each answer.')}</p>
    <div class="examples">${[pair('삼성전자 매출, 2022년과 2023년 비교', 'Compare Samsung revenue in FY2022 and FY2023'), pair('같은 질문을 NAVER로 이어 가기', 'Continue the same question with NAVER'), pair('검증 자료에 없는 연구개발비 질문', 'Ask about R&D outside the verified collection')].map((label, i) => `<button data-example="${i}"><span>${label}</span><small>${pair('녹화 보기', 'View recording')}</small></button>`).join('')}</div>
    <p class="record-meta">${pair('시작 화면의 디자인 제안입니다. 위 예시는 실제 실행 기록을 엽니다. 새 질문을 전송하거나 저장하지 않습니다.', 'This is a proposed entry screen. Examples open actual execution recordings. This preview does not submit or save new questions.')}</p></div>
    <aside class="entry-coverage"><table class="coverage-table"><caption>${pair('질문할 수 있는 자료', 'Available filing coverage')}</caption><thead><tr><th>${pair('회사', 'Company')}</th><th>${pair('회계연도', 'Fiscal years')}</th></tr></thead><tbody><tr><td>${pair('삼성전자', 'Samsung')}</td><td>2022, 2023</td></tr><tr><td>NAVER</td><td>2023</td></tr><tr><td>Microsoft</td><td>2023, 2024</td></tr></tbody></table>
    <p>${pair('연결 매출 · 영업이익 · 순이익', 'Consolidated revenue · Operating income · Net income')}</p><p>${pair('검증된 과거 자료를 사용합니다. 최신 공시를 자동으로 가져오지 않으며, 자료에 없는 수치는 답변하지 않습니다.', 'Uses a verified historical collection. New filings are not downloaded automatically, and unsupported figures are withheld.')}</p>
    <details><summary>${pair('실제 앱에서 처음 사용하기', 'First use in the local app')}</summary><p>${pair('로컬 앱을 실행한 뒤 “삼성전자 2023년 매출은?”을 입력합니다. 답변의 수치를 눌러 근거를 확인하고, “2022년과 비교해 줘”로 이어 갑니다. 마지막으로 조사를 저장하고 기록에서 다시 열어 보세요.', 'Start the local app and ask “What was Samsung revenue in FY2023?” Select a figure to inspect its evidence, then ask “Compare it with FY2022.” Save the investigation and reopen it from History.')}</p></details></aside></div>`;
}

function draw() {
  document.querySelector('.skip-link').textContent = pair('조사 화면으로 건너뛰기', 'Skip to investigation');
  document.querySelector('.site-header nav').setAttribute('aria-label', pair('화면 선택', 'Choose a screen'));
  document.querySelector('[data-screen=replay]').textContent = pair('녹화된 조사', 'Recorded investigation');
  document.querySelector('[data-screen=local]').textContent = pair('시작 화면', 'Start screen');
  document.querySelectorAll('[data-screen]').forEach(b => b.setAttribute('aria-pressed', b.dataset.screen === screen));
  document.querySelector('#icon-link').textContent = pair('F 아이콘 제안', 'F icon proposal');
  document.querySelector('#icon-link').href = `icons-final.html?lang=${language}&v=1`;
  document.querySelector('#scope-note').textContent = pair('최종 디자인 제안 · 실제 실행 기록으로 화면을 살펴보세요', 'Final design proposal · Explore the screens with actual execution recordings');
  document.querySelector('#close-source').textContent = pair('닫기', 'Close');
  if (screen === 'local') {
    content.innerHTML = entry();
    content.querySelectorAll('[data-example]').forEach(b => b.onclick = () => selectScenario(Number(b.dataset.example)));
    return;
  }
  if (failed) {
    content.innerHTML = `<p role="alert">${pair('녹화 자료를 불러오지 못했습니다. 다시 불러와 주세요.', 'Could not load the recording. Please reload it.')}</p><button class="action" id="reload">${pair('다시 불러오기', 'Reload')}</button>`;
    document.querySelector('#reload').onclick = load;
    return;
  }
  if (!recording) {
    content.innerHTML = `<p role="status">${pair('녹화된 조사를 불러오는 중입니다.', 'Loading recorded investigations.')}</p>`;
    return;
  }
  if (!recording.investigations?.length) {
    content.innerHTML = `<p>${pair('녹화된 조사가 없습니다. 시작 화면에서 지원 자료를 확인해 주세요.', 'There are no recorded investigations. Check the supported coverage on the start screen.')}</p>`;
    return;
  }
  const turns = recording.investigations[scenario].turns;
  turn = Math.min(turn, turns.length - 1);
  const t = turns[turn], answer = t.answer, figures = answer.figures || [];
  selectedFigure = Math.min(selectedFigure, Math.max(0, figures.length - 1));
  const questions = ['How did Samsung revenue change between FY2022 and FY2023?', turn === 0 ? 'What was Samsung revenue in FY2023?' : 'What about NAVER?', 'What were Samsung R&D expenses in FY2023?'];
  const explanation = [pair('증감률은 (2023년 매출 − 2022년 매출) ÷ 2022년 매출 × 100입니다. 각 입력값의 원문 단위와 회계연도를 확인할 수 있습니다.', 'Change is (FY2023 revenue − FY2022 revenue) ÷ FY2022 revenue × 100. Each input retains its original unit and fiscal year.'), pair('회사 이름만 바꾸고, 앞 질문의 매출과 2023년을 유지합니다. 표시한 금액은 해당 회사의 공시에 연결됩니다.', 'The follow-up changes the company while retaining revenue and FY2023. The displayed value links to that company’s filing.'), pair('삼성전자 2023년 연구개발비는 현재 검증 자료에 없습니다. 해당 수치를 0으로 취급하거나 다른 지표로 대체하지 않습니다.', 'Samsung FY2023 R&D is outside the verified collection. It is not treated as zero or replaced by a different metric.')][scenario];
  content.innerHTML = `<div class="research-heading"><div><p class="eyebrow">${pair('녹화된 조사', 'Recorded investigation')} / 0${scenario + 1}</p><h1>${[pair('삼성전자 매출 비교', 'Samsung revenue comparison'), pair('회사를 바꿔 이어 묻기', 'A follow-up about another company'), pair('근거가 부족한 질문', 'When evidence is missing')][scenario]}</h1></div><small>${pair('과거 회계연도 · 검증 자료 기준', 'Historical fiscal years · Verified collection')}</small></div>
    <div class="scenario-controls">${names().map((label, i) => `<button data-scenario="${i}" aria-pressed="${scenario === i}">${label}</button>`).join('')}</div>
    <div class="research-grid" style="margin-top:32px"><article><div class="question"><span>${pair('질문', 'Question')} ${turn + 1} / ${turns.length}</span>${esc(language === 'ko' ? t.question : questions[scenario])}</div>
    <p class="answer-text">${esc(answer['answer_' + language])}</p><div class="figure-list">${figures.map((f, i) => `<button class="figure-row" data-source="${i}" aria-pressed="${selectedFigure === i}"><span class="period">FY${esc(f.period)}<br>${pair('연결 매출', 'Consolidated revenue')}</span><span><strong>${(Number(f.value) / 1e12).toFixed(2)} ${pair('조 원', 'trillion KRW')}</strong><small>${pair('원문 근거 보기', 'Inspect original evidence')}</small></span></button>`).join('')}</div>
    ${(answer.calculated || []).map(c => `<div class="calculation"><span>${pair('2022년 대비 증감률', 'Change from FY2022')}</span><strong>${esc(c.percentage_change)}%</strong></div>`).join('')}
    <details><summary>${pair('확인한 자료와 계산 방식', 'Checked scope and calculation')}</summary><p>${explanation}</p></details><p class="record-meta">${pair('실제 실행 기록', 'Actual execution recording')} · 2026-09-08 · ${t.wall_seconds.toFixed(2)}s</p>
    ${turns.length > 1 ? `<button class="action" id="turn-switch">${turn === 0 ? pair('다음 질문: 네이버는?', 'Next: What about NAVER?') : pair('이전 질문 보기', 'Previous question')}</button>` : ''}</article>
    <aside class="evidence-panel">${figures.length ? source(figures[selectedFigure]) : `<p class="eyebrow">${pair('확인한 범위', 'Checked scope')}</p><h3>${pair('근거 없는 수치는<br>표시하지 않습니다', 'Figures are withheld<br>without evidence')}</h3><p>${pair('현재 검증 자료에 포함되지 않은 지표입니다. 공시 전체에 해당 지표가 없다는 뜻은 아닙니다.', 'This metric is outside the verified collection. It may still appear in the full filing.')}</p>`}</aside></div>`;
  content.querySelectorAll('[data-scenario]').forEach(b => b.onclick = () => selectScenario(Number(b.dataset.scenario)));
  content.querySelectorAll('[data-source]').forEach(b => b.onclick = () => {
    selectedFigure = Number(b.dataset.source);
    content.querySelectorAll('[data-source]').forEach(row => row.setAttribute('aria-pressed', row === b));
    content.querySelector('.evidence-panel').innerHTML = source(figures[selectedFigure]);
    if (matchMedia('(max-width:800px)').matches) {
      document.querySelector('#source-content').innerHTML = source(figures[selectedFigure]);
      dialog.setAttribute('aria-label', pair('공시 원문 근거', 'Original filing evidence'));
      dialog.showModal();
    }
  });
  const turnSwitch = content.querySelector('#turn-switch');
  if (turnSwitch) turnSwitch.onclick = () => { turn = turn === 0 ? 1 : 0; selectedFigure = 0; draw(); };
}

async function load() {
  failed = false; recording = undefined; draw();
  try {
    const response = await fetch('assets/recording.json');
    if (!response.ok) throw Error('Recording unavailable');
    recording = await response.json();
  } catch { failed = true; }
  draw();
}
document.querySelectorAll('[data-screen]').forEach(b => b.onclick = () => { screen = b.dataset.screen; draw(); });
document.querySelector('#close-source').onclick = () => dialog.close();
setup(draw);
load();
