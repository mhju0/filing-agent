import { chromium } from '../../verification/node_modules/playwright/index.mjs';
import AxeBuilder from '../../verification/node_modules/@axe-core/playwright/dist/index.mjs';
import assert from 'node:assert/strict';
import { readFile, mkdir, writeFile } from 'node:fs/promises';

const base = process.env.VERIFY_BASE || 'http://127.0.0.1:8765';
const out = process.env.VERIFY_OUT || '.local/architecture-implementation/browser-state';
await mkdir(out, { recursive: true });
const recording = JSON.parse(await readFile(process.env.RECORDING_FIXTURE || 'slice/replay-release/recording.json', 'utf8'));
const a = structuredClone(recording.investigations[0]);
const b = structuredClone(recording.investigations[1]);
a.turns = [a.turns[0]];
b.turns = [b.turns[0]];
a.saved = b.saved = false;
a.turns[0].question = 'Investigation A'; b.turns[0].question = 'Investigation B';
const completed = structuredClone(a.turns[0]);
a.turns[0].status = 'running';
let running = true, aReads = 0, releaseLate, lateStarted;
const late = new Promise(resolve => { lateStarted = resolve; });
const blocked = new Promise(resolve => { releaseLate = resolve; });
let retryCalls = 0, cancelled = false;
let releaseCreate, createStarted;
const creating = new Promise(resolve => { createStarted = resolve; });
const createWait = new Promise(resolve => { releaseCreate = resolve; });
let historyCalls = 0, releaseHistory, historyReturned;
const historyWait = new Promise(resolve => { releaseHistory = resolve; });
const firstHistoryReturned = new Promise(resolve => { historyReturned = resolve; });
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const errors = [], checks = [];
try {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  await context.addInitScript(id => {
    localStorage.setItem('filing-language', 'en');
    if (!localStorage.getItem('filing-investigation')) localStorage.setItem('filing-investigation', id);
  }, a.id);
  await context.route('**/api/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const send = (body, status = 200) => route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(body) });
    if (path === '/api/investigations' && route.request().method() === 'POST') {
      createStarted(); await createWait;
      return send({ ...structuredClone(b), id: 'new-test', turns: [] });
    }
    if (path === '/api/investigations/new-test') return send({ ...structuredClone(b), id: 'new-test', turns: [] });
    if (path === '/api/session') return send({ token: 'test', running });
    if (path === '/api/history') {
      historyCalls++;
      if (historyCalls === 1) {
        await historyWait;
        await send([a, b]);
        historyReturned();
        return;
      }
      return send([a, b]);
    }
    if (path.endsWith('/cancel')) { cancelled = true; return send({}); }
    if (path.endsWith('/retry-storage')) {
      retryCalls++;
      if (retryCalls === 1) return send({ detail: 'Storage unavailable; retry later' }, 503);
      a.turns[0] = structuredClone(completed);
      return send(a);
    }
    if (path.endsWith('/discard-unstored')) {
      a.turns[0].status = 'discarded'; delete a.turns[0].answer;
      return send(a);
    }
    if (path === '/api/investigations/' + a.id) {
      aReads++;
      if (aReads === 2) {
        const old = structuredClone(a);
        lateStarted(); await blocked; return send(old);
      }
      return send(a);
    }
    if (path === '/api/investigations/' + b.id) return send(b);
    throw new Error('Unexpected request: ' + path);
  });
  const page = await context.newPage();
  page.on('pageerror', e => errors.push(e.message));
  await page.goto(base);
  await page.getByRole('heading', { name: 'Investigation A', exact: true }).waitFor();
  await late;
  await page.getByRole('button', { name: 'History', exact: true }).click();
  const loadingHistory = page.getByRole('dialog', { name: 'History' });
  await loadingHistory.getByRole('status').filter({ hasText: 'Loading history.' }).waitFor();
  await loadingHistory.getByRole('button', { name: 'Close' }).click();
  releaseHistory();
  await firstHistoryReturned;
  assert.equal(await page.getByRole('dialog', { name: 'History' }).count(), 0);
  await page.getByRole('button', { name: 'History', exact: true }).click();
  await page.locator('.history-row').filter({ hasText: 'Investigation B' }).click();
  await page.getByRole('textbox').fill('Draft belongs to B');
  await page.locator('article').first().locator('.figure').first().click();
  const bEvidence = await page.locator('aside.evidence').innerText();
  assert.equal(await page.getByRole('button', { name: 'Ask', exact: true }).isDisabled(), true);
  a.turns[0] = structuredClone(completed); running = false; releaseLate();
  await page.waitForFunction(() => ![...document.querySelectorAll('button')].find(b => b.textContent === 'Ask')?.disabled);
  assert.equal(await page.getByRole('heading', { name: 'Investigation B', exact: true }).count(), 1);
  assert.equal(await page.getByRole('textbox').inputValue(), 'Draft belongs to B');
  assert.equal(await page.locator('aside.evidence').innerText(), bEvidence);
  assert.equal(cancelled, false);
  checks.push('Closing History while its request is pending cannot reopen it; a fresh open succeeds');
  checks.push('Late A response preserves B conversation, draft and evidence; navigation does not cancel A; global execution blocks new inference');

  await page.getByRole('button', { name: 'History', exact: true }).click();
  const historyModal = page.getByRole('dialog', { name: 'History' });
  await historyModal.locator('.history-item').filter({ hasText: 'Investigation B' }).getByRole('button', { name: 'Delete this investigation' }).click();
  assert.equal(await page.getByRole('dialog').count(), 1);
  assert.equal(await page.locator('.modal-layer[aria-hidden="true"][inert]').count(), 1);
  await page.keyboard.press('Escape');
  await historyModal.waitFor();
  await page.locator('.history-row').filter({ hasText: 'Investigation A' }).click();
  a.turns[0].status = 'storage_failed';
  await page.getByRole('button', { name: 'Retry storage', exact: true }).waitFor();
  assert.equal(await page.getByRole('button', { name: 'Save investigation', exact: true }).count(), 0);
  assert.equal(await page.getByRole('button', { name: 'New investigation', exact: true }).isEnabled(), true);
  await page.getByRole('button', { name: 'Retry storage', exact: true }).click();
  await page.getByRole('alert').filter({ hasText: 'Storage unavailable' }).waitFor();
  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 1000 });
    for (const lang of ['ko', 'en']) {
      await page.getByRole('button', { name: lang === 'ko' ? '한국어' : 'English', exact: true }).click();
      for (const dark of [false, true]) {
        await page.emulateMedia({ colorScheme: dark ? 'dark' : 'light', reducedMotion: 'reduce' });
        await page.evaluate(() => document.fonts.ready);
        await page.evaluate(() => new Promise(resolve =>
          requestAnimationFrame(() => requestAnimationFrame(resolve)),
        ));
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
        const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
        assert.deepEqual(axe.violations.map(v => v.id), []);
        await page.screenshot({ path: `${out}/storage-${lang}-${width}-${dark ? 'dark' : 'light'}.png`, fullPage: true });
      }
    }
  }
  await page.getByRole('button', { name: 'Retry storage', exact: true }).click();
  await page.getByRole('button', { name: 'Save investigation', exact: true }).waitFor();
  assert.equal(await page.locator('article').count(), 1);
  checks.push('Storage failure retains figures; repeated explicit retry restores one turn; KO/EN light/dark recovery passes axe and reflow at 1440/390/320');
  a.turns[0].status = 'storage_failed';
  await page.getByRole('button', { name: 'Discard unstored result', exact: true }).click();
  await page.getByRole('button', { name: 'Confirm discard', exact: true }).click();
  await page.getByText('Unstored result discarded. Earlier turns are preserved.', { exact: true }).waitFor();
  assert.equal(await page.locator('[role="dialog"]').count(), 0);
  checks.push('Discard requires confirmation and removes only the unstored result');
  await page.getByRole('button', { name: 'New investigation', exact: true }).click();
  await creating;
  assert.equal(await page.getByRole('textbox').isDisabled(), true);
  releaseCreate();
  await page.getByRole('textbox').fill('Draft written after creation');
  await page.reload();
  await page.getByRole('textbox').waitFor();
  assert.equal(await page.getByRole('textbox').inputValue(), 'Draft written after creation');
  checks.push('Composer waits for new investigation creation; its draft is present immediately on reload');
  await context.close();

  const replayContext = await browser.newContext();
  let liveRequests = 0;
  await replayContext.route('**/*', async route => {
    const url = new URL(route.request().url());
    if (url.pathname.startsWith('/api/')) { liveRequests++; return route.abort(); }
    if (url.pathname === '/recording.json') return route.fulfill({ contentType: 'application/json', body: JSON.stringify(recording) });
    if (url.pathname === '/') {
      const response = await route.fetch();
      return route.fulfill({ response, body: (await response.text()).replace('<html lang="ko">', '<html lang="ko" data-mode="replay">') });
    }
    return route.continue();
  });
  const replayPage = await replayContext.newPage();
  replayPage.on('pageerror', e => errors.push(e.message));
  await replayPage.goto(base + '/#scenario=1&turn=1');
  await replayPage.locator('article').nth(1).waitFor();
  assert.equal(await replayPage.getByRole('textbox').count(), 0);
  await replayPage.getByRole('button', { name: 'English', exact: true }).click();
  await replayPage.getByRole('combobox').selectOption('0');
  assert.equal(await replayPage.locator('article').count(), 1);
  await replayPage.reload();
  await replayPage.locator('article').first().waitFor();
  assert.equal(liveRequests, 0);
  checks.push('Replay restores URL selection, resets turn on scenario switch, has no composer and makes no live requests');
  await replayContext.close();
  assert.deepEqual(errors, []);
  await writeFile(`${out}/verification.json`, JSON.stringify({ status: 'PASS', checks, errors }, null, 2));
  console.log(checks.join('\n'));
} finally { releaseLate?.(); releaseHistory?.(); await browser.close(); }
