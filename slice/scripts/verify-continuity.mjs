import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { chromium, webkit } from "../../verification/node_modules/playwright/index.mjs";

const base = process.env.VERIFY_BASE || "http://127.0.0.1:4177";
const out = process.env.VERIFY_OUT || "private/continuity/browser";
const recording = JSON.parse(await readFile(
  process.env.RECORDING_FIXTURE || "slice/replay-release/recording.json",
  "utf8",
));
await mkdir(out, { recursive: true });

async function replayPage(browser, options) {
  const context = await browser.newContext(options);
  await context.route("**/*", async route => {
    const url = new URL(route.request().url());
    if (url.pathname === "/recording.json") {
      return route.fulfill({ contentType: "application/json", body: JSON.stringify(recording) });
    }
    if (url.pathname === "/") {
      const response = await route.fetch();
      return route.fulfill({
        response,
        body: (await response.text()).replace(
          '<html lang="ko">',
          '<html lang="ko" data-mode="replay">',
        ),
      });
    }
    return route.continue();
  });
  const page = await context.newPage();
  await page.goto(base + "/");
  await page.locator(".turn").first().waitFor();
  return { context, page };
}

const checks = [];
const errors = [];
const observedRequests = new Set();
const chrome = await chromium.launch({ channel: "chrome", headless: true });
try {
  {
    const { context, page } = await replayPage(chrome, {
      viewport: { width: 1440, height: 900 },
      reducedMotion: "no-preference",
      colorScheme: "light",
    });
    page.on("pageerror", error => errors.push(error.message));
    page.on("request", request => observedRequests.add(request.url()));
    await page.evaluate(() => document.addEventListener("securitypolicyviolation", event => {
      console.error(`CSP violation: ${event.violatedDirective} ${event.blockedURI}`);
    }));
    page.on("console", message => {
      if (message.type() === "error") errors.push(message.text());
    });
    await page.getByRole("button", { name: "English", exact: true }).click();
    await page.getByRole("button", { name: "Close", exact: true }).dispatchEvent("click");
    await page.waitForTimeout(500);
    const figure = page.locator(".figure").first();
    await figure.hover();
    await page.mouse.down();
    assert.notEqual(await figure.evaluate(node => getComputedStyle(node).transform), "none");
    await page.mouse.up();
    await figure.dispatchEvent("click");
    await page.waitForTimeout(32);
    const opening = await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform);
    assert.notEqual(opening, "none");
    await page.locator("aside.evidence .panel-head button").dispatchEvent("click");
    const beforeCloseFrame = await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform);
    await page.waitForTimeout(16);
    const afterCloseFrame = await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform);
    const translateX = value => value === "none" ? 0 : Number(value.match(/matrix\([^,]+,[^,]+,[^,]+,[^,]+,\s*([^,]+)/)?.[1]);
    assert.ok(Math.abs(translateX(afterCloseFrame) - translateX(beforeCloseFrame)) < 10);
    assert.equal(await page.locator("aside.evidence[aria-hidden=true][inert]").count(), 1);
    await figure.dispatchEvent("click");
    const beforeReopenFrame = await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform);
    await page.waitForTimeout(16);
    const afterReopenFrame = await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform);
    assert.ok(Math.abs(translateX(afterReopenFrame) - translateX(beforeReopenFrame)) < 10);
    await page.waitForTimeout(500);
    assert.equal(await page.locator("aside.evidence").count(), 1);
    assert.equal(await page.locator(".figure.selected").count(), 1);
    assert.equal(await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).transform), "none");
    assert.equal(await page.locator("aside.evidence").evaluate(node => getComputedStyle(node).opacity), "1");
    await page.screenshot({ path: `${out}/desktop-en-light.png`, fullPage: false });
    checks.push("Desktop press responds on pointer down; evidence spring has an in-flight presentation and rapid close/reopen settles to one selected source");
    await context.close();
  }

  {
    const { context, page } = await replayPage(chrome, {
      viewport: { width: 390, height: 620 },
      reducedMotion: "no-preference",
      colorScheme: "dark",
    });
    page.on("pageerror", error => errors.push(error.message));
    page.on("request", request => observedRequests.add(request.url()));
    await page.getByRole("button", { name: "English", exact: true }).click();
    const figure = page.locator(".figure").first();
    await figure.click();
    await page.getByRole("dialog").waitFor();
    const content = page.locator(".evidence-content");
    await content.evaluate(node => { node.scrollTop = 120; });
    await page.waitForTimeout(16);
    const before = await content.evaluate(node => node.scrollTop);
    await page.setViewportSize({ width: 851, height: 620 });
    await page.locator("aside.evidence").waitFor();
    assert.equal(await page.locator("aside.evidence").count(), 1);
    await page.setViewportSize({ width: 390, height: 620 });
    await page.getByRole("dialog").waitFor();
    const after = await page.locator(".evidence-modal .evidence-content").evaluate(node => node.scrollTop);
    assert.ok(Math.abs(after - before) <= 1, `evidence scroll changed from ${before} to ${after}`);
    await page.getByRole("button", { name: "Close", exact: true }).click();
    assert.equal(await page.getByRole("dialog").count(), 0);
    assert.equal(await page.locator(".modal-layer[aria-hidden=true][inert]").count(), 1);
    await figure.click();
    assert.equal(await page.getByRole("dialog").count(), 1);
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.waitForTimeout(60);
    assert.equal(await page.locator(".modal-surface").last().evaluate(node => getComputedStyle(node).transform), "none");
    assert.equal(await page.locator(".modal-layer").last().evaluate(node => getComputedStyle(node).opacity), "1");
    assert.equal(await page.locator(".modal-surface").last().evaluate(node => getComputedStyle(node).opacity), "1");
    assert.match(
      await page.locator(".modal-surface").last().evaluate(node => getComputedStyle(node).backgroundColor),
      /^rgb\(/,
    );
    await page.screenshot({ path: `${out}/mobile-en-dark-reduced.png`, fullPage: false });
    checks.push("Evidence survives the 850/851 layout boundary with reading position; close releases modal semantics immediately; reopen retargets; changing to reduced motion settles spatial travel");
    await context.close();
  }

  {
    const { context, page } = await replayPage(chrome, {
      viewport: { width: 320, height: 760 },
      reducedMotion: "reduce",
      colorScheme: "light",
    });
    await page.locator(".figure").first().click();
    await page.waitForTimeout(60);
    assert.equal(await page.locator(".modal-surface").evaluate(node => getComputedStyle(node).transform), "none");
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
    await page.waitForTimeout(32);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    assert.equal(await page.getByRole("dialog").isVisible(), true);
    checks.push("Reduced motion starts without spatial travel; the 320px layout reflows without horizontal overflow at default and 200% text size");
    await context.close();
  }

  let webkitResult = "UNAVAILABLE";
  let wk = null;
  try {
    wk = await webkit.launch({ headless: true });
  } catch (error) {
    webkitResult = `UNAVAILABLE: ${error.message}`;
  }
  if (wk) {
    try {
    const { context, page } = await replayPage(wk, {
      viewport: { width: 390, height: 760 },
      reducedMotion: "no-preference",
      colorScheme: "light",
    });
    await page.locator(".figure").first().click();
    await page.getByRole("dialog").waitFor();
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").count(), 0);
    webkitResult = "PASS";
    checks.push("WebKit mobile evidence opens semantically and Escape closes immediately");
    await context.close();
    } finally {
      await wk.close();
    }
  }

  const unexpectedRequests = [...observedRequests].filter(value => {
    const url = new URL(value);
    return url.origin !== new URL(base).origin || url.pathname.startsWith("/api/");
  });
  assert.deepEqual(unexpectedRequests, []);
  assert.deepEqual(errors, []);
  checks.push("Replay made no live API or foreign request and raised no CSP or browser errors");
  const report = {
    status: "PASS",
    base,
    checks,
    errors,
    unexpectedRequests,
    webkit: webkitResult,
    screenshots: [`${out}/desktop-en-light.png`, `${out}/mobile-en-dark-reduced.png`],
  };
  await writeFile(`${out}/continuity.json`, JSON.stringify(report, null, 2));
  console.log(JSON.stringify(report, null, 2));
} finally {
  await chrome.close();
}
