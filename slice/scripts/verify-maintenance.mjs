import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium } from '../../verification/node_modules/playwright/index.mjs';
import AxeBuilder from '../../verification/node_modules/@axe-core/playwright/dist/index.mjs';

const base = process.env.VERIFY_BASE || 'http://127.0.0.1:4176';
const out = process.env.VERIFY_OUT || '.local/maintenance-browser';
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const checks = [], measurements = [], failures = [];
await writeFile(`${out}/verification.json`, JSON.stringify({ status: 'RUNNING', base }) + '\n');
try {
  for (const lang of ['ko', 'en']) for (const theme of ['light', 'dark']) for (const width of [320, 390, 1440]) {
    const context = await browser.newContext({ viewport: { width, height: 852 }, colorScheme: theme,
      hasTouch: width < 850, isMobile: width < 850, reducedMotion: 'reduce' });
    await context.addInitScript(({ lang, theme }) => {
      localStorage.setItem('filing-language', lang);
      localStorage.setItem('filing-theme', theme);
    }, { lang, theme });
    const page = await context.newPage();
    const errors = [], requests = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('request', request => requests.push(request.url()));
    await page.goto(base);
    await page.getByRole('button', { name: 'English', exact: true }).waitFor();
    await page.evaluate(() => document.fonts.ready);
    const id = `${lang}-${theme}-${width}`;
    measurements.push({ id, ...await page.evaluate(() => ({
      fcpMs: performance.getEntriesByName('first-contentful-paint')[0]?.startTime,
      domContentLoadedMs: performance.getEntriesByType('navigation')[0].domContentLoadedEventEnd,
      encodedBodyBytes: performance.getEntriesByType('resource').reduce((sum, entry) => sum + entry.encodedBodySize, 0),
    })) });
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('.skip').evaluate(node => node === document.activeElement), true);
    await page.keyboard.press('Enter');
    await page.keyboard.press('Tab');
    assert.equal(await page.locator('#main-pane').evaluate(node => node.contains(document.activeElement)), true);
    const check = async surface => {
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: `${out}/${id}-${surface}.png`, fullPage: true });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      const splitWords = await page.evaluate(() => {
        const split = new Set();
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        for (let node = walker.nextNode(); node; node = walker.nextNode()) {
          const parent = node.parentElement;
          if (!parent || parent.closest('.sr-only, [hidden], [aria-hidden="true"], [inert]') ||
              !parent.getClientRects().length || getComputedStyle(parent).visibility === 'hidden') continue;
          for (const match of node.textContent.matchAll(/[가-힣]+/g)) {
            const range = document.createRange();
            range.setStart(node, match.index);
            range.setEnd(node, match.index + match[0].length);
            const lines = new Set([...range.getClientRects()].filter(r => r.width && r.height).map(r => Math.round(r.y)));
            if (lines.size > 1) split.add(match[0]);
          }
        }
        return [...split];
      });
      const axe = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21aa']).analyze();
      const violations = axe.violations.map(v => ({ id: v.id, targets: v.nodes.map(n => n.target) }));
      if (overflow || splitWords.length || violations.length) failures.push({ id, surface, overflow, splitWords, violations });
      else checks.push(`${id} ${surface}: reflow, Korean word boundaries, axe, screenshot`);
    };
    const audit = async surface => {
      await check(surface);
      if (width === 320) {
        await page.evaluate(() => { document.documentElement.style.fontSize = '200%'; });
        await check(surface + '-200pct');
        await page.evaluate(() => { document.documentElement.style.fontSize = ''; });
      }
    };
    await audit('overview');
    await page.getByRole('button', { name: lang === 'ko' ? '수치 장부' : 'Ledger', exact: true }).click();
    await page.locator('.ledger .ledger-table').first().waitFor();
    assert.equal(await page.locator('.figures-table .value-button').count(), 15);
    await audit('ledger');
    await page.getByRole('button', { name: lang === 'ko' ? '공시 가이드' : 'Guide', exact: true }).click();
    await audit('guide');
    await page.getByRole('button', { name: lang === 'ko' ? '녹화된 조사' : 'Recorded runs', exact: true }).click();
    await page.locator('.figure-value').first().waitFor();
    await audit('recorded-run');
    assert.deepEqual(errors, [], id + ' browser errors');
    assert.equal(requests.some(url => new URL(url).origin !== new URL(base).origin || new URL(url).pathname.startsWith('/api/')), false);
    await context.close();
  }
  await writeFile(`${out}/verification.json`, JSON.stringify({ status: failures.length ? 'FAIL' : 'PASS', base, checks, failures, measurements }, null, 2) + '\n');
  assert.deepEqual(failures, [], 'Every rendered surface must pass');
  console.log(`MAINTENANCE PASS: ${checks.length} rendered surfaces; keyboard skip; static-only requests`);
} catch (error) {
  await writeFile(`${out}/verification.json`, JSON.stringify({ status: 'FAIL', base, error: error.message, checks, failures, measurements }, null, 2) + '\n');
  throw error;
} finally {
  await browser.close();
}
