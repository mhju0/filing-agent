import { chromium } from '../../verification/node_modules/playwright/index.mjs';
import { writeFile, mkdir } from 'node:fs/promises';
import assert from 'node:assert/strict';

const out = process.env.CAPTURE_OUT || 'docs/audits/2026-09-10-final-polish';
const base = process.env.CAPTURE_BASE || 'http://127.0.0.1:8765';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 }, colorScheme: 'light', reducedMotion: 'reduce',
  recordVideo: { dir: '.local/video', size: { width: 1280, height: 900 } },
});
const page = await context.newPage();
const moments = [];
const started = Date.now();
const moment = (ko, en) => moments.push({ seconds: (Date.now() - started) / 1000, ko, en });
const current = async () => {
  const id = await page.evaluate(() => localStorage.getItem('filing-investigation'));
  const response = await page.request.get(base + '/api/investigations/' + id);
  assert.equal(response.status(), 200);
  return response.json();
};
try {
  await page.goto(base);
  await page.getByRole('textbox').waitFor();
  await page.getByRole('button', { name: '한국어', exact: true }).click();
  for (const [index, question] of ['삼성전자 2023년 매출액은?', '2022년과 비교하면 얼마나 감소했어?'].entries()) {
    await page.getByRole('textbox').fill(question);
    moment(index ? '회사를 반복하지 않고 전년과 비교합니다' : '삼성전자의 2023년 매출액을 묻습니다', index ? 'Compare with the previous year without repeating the company' : 'Ask for Samsung revenue in FY2023');
    await page.getByRole('button', { name: '질문', exact: true }).click();
    await page.locator('article').nth(index).locator('.figure').first().waitFor({ timeout: 120000 });
    await page.getByRole('button', { name: '조사 저장', exact: true }).waitFor();
    await page.locator('article').nth(index).locator('.figure').last().click();
    moment('수치와 연결된 원문 발췌를 확인합니다', 'Inspect the original excerpt linked to the reported figure');
    await page.waitForTimeout(1800);
  }
  const comparison = await current();
  assert.equal(comparison.turns[1].answer.calculated[0].percentage_change, '-14.33');
  await page.locator('article').last().locator('.formula summary').click();
  moment('증감률은 검증된 두 수치로 계산합니다', 'The change is calculated from the two verified figures');
  await page.screenshot({ path: out + '/actual-run.png' });
  await page.waitForTimeout(2000);
  await page.getByRole('button', { name: '조사 저장', exact: true }).click();
  await page.getByRole('button', { name: '원본 근거로 계속', exact: true }).waitFor();
  const saved = await current();
  await page.reload();
  await page.getByRole('button', { name: '원본 근거로 계속', exact: true }).waitFor();
  assert.deepEqual(await current(), saved);
  moment('저장한 결과를 다시 열어도 원래 답변과 근거가 유지됩니다', 'Reopening preserves the saved answers and evidence');
  await page.waitForTimeout(1500);
  await page.getByRole('button', { name: '원본 근거로 계속', exact: true }).click();
  await page.getByRole('textbox').waitFor();
  const continued = await current();
  assert.notEqual(continued.id, saved.id);
  assert.equal(continued.snapshot_id, saved.snapshot_id);
  assert.equal(continued.turns.length, 2);
  moment('원본을 보존한 채 새 조사에서 질문을 이어갑니다', 'Continue in a new investigation while preserving the original');
  await page.waitForTimeout(1800);
  await writeFile(out + '/actual-run.json', JSON.stringify({
    kind: 'Unedited browser capture with real local inference',
    captured_at: new Date().toISOString(),
    investigation: { id: saved.id, snapshot_id: saved.snapshot_id, turn_ids: saved.turns.map(turn => turn.id) },
    checks: ['exact -14.33% comparison', 'saved reload unchanged', 'continued with original snapshot'],
    continued_id: continued.id, moments,
  }, null, 2) + '\n');
  const stamp = seconds => new Date(Math.round(seconds * 1000)).toISOString().slice(11, 23);
  for (const lang of ['ko', 'en']) {
    const duration = (Date.now() - started) / 1000;
    await writeFile(`${out}/actual-run-${lang}.vtt`, 'WEBVTT\n\n' + moments.map((m, i) => `${stamp(m.seconds)} --> ${stamp(moments[i + 1]?.seconds || duration)}\n${m[lang]}\n`).join('\n'));
  }
  await context.close();
  await page.video().saveAs(out + '/actual-run.webm');
  console.log('Actual comparison, source inspection, saved reload and continuation captured');
} finally {
  await browser.close();
}
