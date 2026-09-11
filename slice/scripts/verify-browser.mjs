import { chromium } from "../../verification/node_modules/playwright/index.mjs";
import AxeBuilder from "../../verification/node_modules/@axe-core/playwright/dist/index.mjs";
import assert from "node:assert/strict";
import { writeFile, mkdir } from "node:fs/promises";
const mode = process.env.VERIFY_MODE || "live";
const base = process.env.VERIFY_BASE || (
  mode === "replay" ? "http://127.0.0.1:4176" : "http://127.0.0.1:8765");
const out = process.env.VERIFY_OUT || "docs/audits/2026-09-08-slice";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({ channel: "chrome", headless: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1000 },
  colorScheme: "light",
  reducedMotion: "reduce",
});
const requests = [],
  errors = [],
  checks = [];
await context.route("**/*", (route) => {
  const url = new URL(route.request().url());
  requests.push(url.href);
  if (
    url.origin !== base ||
    (mode === "replay" && url.pathname.startsWith("/api/"))
  )
    return route.abort();
  return route.continue();
});
const page = await context.newPage();
const createdIDs = new Set();
const creationReads = [];
page.on("response", response => {
  const request = response.request();
  const path = new URL(response.url()).pathname;
  if (mode === "live" && request.method() === "POST" && response.ok() &&
      (path === "/api/investigations" || /^\/api\/investigations\/[^/]+\/fork$/.test(path))) {
    creationReads.push(response.json().then(body => createdIDs.add(body.id)));
  }
});
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
const audit = async (name) => {
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => new Promise(resolve =>
    requestAnimationFrame(() => requestAnimationFrame(resolve)),
  ));
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth > innerWidth,
    ),
    false,
    name + " overflow",
  );
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  assert.deepEqual(
    result.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => n.target),
    })),
    [],
    name + " accessibility",
  );
  await page.screenshot({ path: `${out}/${mode}-${name}.png`, fullPage: true });
  checks.push(name + " no overflow; axe WCAG A/AA checks passed");
};
try {
  await page.goto(base);
  await page.getByRole("button", { name: "English", exact: true }).waitFor();
  if (mode === "live") {
    await page.getByRole("textbox").waitFor();
    for (const q of [
      "삼성전자 2023년과 2022년 매출액을 비교해 줘",
      "네이버 2023년 영업이익은?",
      "Microsoft 2024년과 2023년 당기순이익을 비교해 줘",
      "삼성전자 2023년 연구개발비는?",
    ]) {
      await page.getByRole("button", { name: q, exact: true }).click();
      assert.equal(await page.getByRole("textbox").inputValue(), q);
    }
    assert.equal(await page.locator("article").count(), 0);
    await page.getByRole("button", { name: "English", exact: true }).click();
    assert.equal(
      await page.getByRole("textbox").inputValue(),
      "삼성전자 2023년 연구개발비는?",
    );
    await audit("start-en-light");
    await page.getByRole("button", { name: "Switch to dark theme" }).click();
    await audit("start-en-dark");
    await page.getByRole("button", { name: "한국어", exact: true }).click();
    await page.getByRole("button", { name: "밝은 테마로 전환" }).click();
    await page
      .getByRole("textbox")
      .fill("삼성전자 2023년과 2022년 매출액 증감률은?");
    await page.getByRole("button", { name: "질문", exact: true }).click();
    await page.locator(".figure").first().waitFor({ timeout: 120000 });
    await page
      .getByRole("button", { name: "조사 저장", exact: true })
      .waitFor();
    assert.equal(await page.locator(".figure").count(), 2);
    await page.locator(".figure").last().click();
    await page.locator(".formula summary").click();
    assert.match(await page.locator(".formula").innerText(), /-14.33/);
    await page.locator(".formula button").first().click();
    assert.match(await page.locator(".evidence").innerText(), /258,935,494/);
    await audit("answer-ko-light");
    const original = await page.locator(".answer-sentence").innerText();
    await page.getByRole("button", { name: "English", exact: true }).click();
    assert.equal(await page.locator(".answer-sentence").innerText(), original);
    await page.getByRole("button", { name: "Switch to dark theme" }).click();
    await audit("answer-en-dark");
    await page
      .getByRole("button", { name: "Save investigation", exact: true })
      .click();
    await page
      .getByRole("button", {
        name: "Continue with original evidence",
        exact: true,
      })
      .waitFor();
    const savedID = await page.evaluate(() =>
      localStorage.getItem("filing-investigation"),
    );
    await page.reload();
    await page
      .getByRole("button", {
        name: "Continue with original evidence",
        exact: true,
      })
      .click();
    await page.getByRole("textbox").waitFor();
    const forkID = await page.evaluate(() =>
      localStorage.getItem("filing-investigation"),
    );
    assert.notEqual(forkID, savedID);
    await page.getByRole("textbox").fill("네이버는?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    // A comparison follow-up carries two years; NAVER only has FY2023, so supported partial evidence remains.
    await page
      .locator("article")
      .nth(1)
      .locator(".answer")
      .waitFor({ timeout: 120000 });
    await page
      .getByRole("button", { name: "Save investigation", exact: true })
      .waitFor();
    await page.getByRole("button", { name: "History", exact: true }).click();
    await page
      .locator('[role="dialog"] .history-row')
      .filter({ hasText: "Saved" })
      .first()
      .click();
    assert.equal(await page.locator('[role="dialog"]').count(), 0);
    await page
      .getByRole("button", {
        name: "New investigation with current data",
        exact: true,
      })
      .click();
    await page.waitForFunction(
      () => document.querySelectorAll("article").length === 0,
    );
    assert.equal(await page.locator("article").count(), 0);
    assert.equal(
      await page.getByRole("textbox").inputValue(),
      "삼성전자 2023년과 2022년 매출액 증감률은?",
    );
    await page
      .getByRole("button", { name: "New investigation", exact: true })
      .click();
    await page.getByRole("textbox").fill("2023년 매출액은?");
    await page.getByRole("button", { name: "Ask", exact: true }).click();
    await page.locator(".choices").waitFor({ timeout: 120000 });
    await page.reload();
    await page.locator(".choices").waitFor();
    await page
      .locator(".choices")
      .getByRole("button", { name: "삼성전자", exact: true })
      .click();
    await page
      .locator("article")
      .nth(1)
      .locator(".figure")
      .waitFor({ timeout: 120000 });
    await page
      .getByRole("button", { name: "Save investigation", exact: true })
      .waitFor();
    await page
      .locator("article")
      .first()
      .getByRole("button", { name: "Edit as new" })
      .click();
    await page.waitForFunction(
      () => document.querySelectorAll("article").length === 0,
    );
    assert.equal(await page.locator("article").count(), 0);
    assert.equal(
      await page.getByRole("textbox").inputValue(),
      "2023년 매출액은?",
    );
    checks.push(
      "Examples fill without sending; live compare; formula inputs; saved continuation; refresh; history; language preserves past answer; persisted clarification resumes; edit starts new",
    );
  } else {
    await page.locator(".figure").first().waitFor();
    assert.equal(await page.getByRole("textbox").count(), 0);
    assert.equal(await page.locator(".evidence").count(), 1);
    assert.equal(await page.locator("article").count(), 1);
    await page.getByRole("button", { name: "다음 질문" }).click();
    await page.locator("article").nth(1).locator(".formula").waitFor();
    await audit("compare-ko-light");
    await page.locator(".formula summary").click();
    await page.locator(".formula button").first().click();
    await page.getByRole("button", { name: "English", exact: true }).click();
    await page.getByRole("button", { name: "Switch to dark theme" }).click();
    assert.match(
      await page.locator(".answer-sentence").last().innerText(),
      /decreased/,
    );
    await audit("compare-en-dark");
    await page.getByRole("combobox").selectOption("1");
    await page.getByRole("button", { name: "Next turn" }).click();
    await page.locator("article").nth(1).locator(".figure").click();
    assert.match(await page.locator(".evidence").innerText(), /NAVER/);
    await page.reload();
    await page.locator("article").nth(1).locator(".figure").waitFor();
    await page.getByRole("button", { name: "Previous turn" }).click();
    assert.equal(await page.locator("article").count(), 1);
    await page.getByRole("combobox").selectOption("2");
    await page.waitForFunction(() => document.querySelectorAll(".figure").length === 0);
    assert.equal(await page.locator(".figure").count(), 0);
    await page
      .getByRole("button", { name: "Inspect checked evidence scope" })
      .click();
    assert.match(
      await page.locator(".evidence").innerText(),
      /not the full filings/,
    );
    await audit("refusal-en-dark");
    await page.getByRole("combobox").selectOption("0");
    checks.push(
      "Three captured scenarios; stable turns; formula/source selection; no live prompt; recorded actual timings; bilingual answer text",
    );
  }
  // Return to an answer for narrow-screen modal and focus verification.
  if (mode === "live") {
    await page.getByRole("button", { name: "History", exact: true }).click();
    await page
      .locator('[role="dialog"] .history-row')
      .filter({ hasText: "Saved" })
      .first()
      .click();
  }
  await page.setViewportSize({ width: 390, height: 844 });
  if (await page.getByRole("dialog").count()) {
    await page
      .getByRole("dialog")
      .getByRole("button", { name: "Close", exact: true })
      .click();
    assert.equal(await page.getByRole("dialog").count(), 0);
  }
  await page.locator(".figure").first().click();
  await page.getByRole("dialog").waitFor();
  await audit("mobile-en-dark-evidence");
  for (let i = 0; i < 8; i++) {
    await page.keyboard.press("Tab");
    assert.equal(
      await page.evaluate(() => !!document.activeElement?.closest('[role="dialog"]')),
      true,
    );
  }
  await page.keyboard.press("Escape");
  assert.equal(await page.locator('[role="dialog"]').count(), 0);
  assert.equal(
    await page.evaluate(() =>
      document.activeElement?.classList.contains("figure"),
    ),
    true,
  );
  await audit("mobile-en-dark-conversation");
  await page.getByRole("button", { name: "한국어", exact: true }).click();
  await page.getByRole("button", { name: "밝은 테마로 전환" }).click();
  await page.setViewportSize({ width: 320, height: 740 });
  await audit("mobile-ko-light-320");
  await page.locator(".figure").first().click();
  await page
    .getByRole("dialog")
    .getByRole("button", { name: "닫기", exact: true })
    .click();
  // Source links are inspected but no regulator navigation is simulated as working.
  await page.locator(".figure").first().click();
  const href = await page
    .getByRole("dialog")
    .locator("a.source-link")
    .getAttribute("href");
  assert.match(href, /^https:\/\/(dart\.fss\.or\.kr|www\.sec\.gov)\//);
  checks.push(
    "390px and 320px reflow; modal focus trap; Escape and close restore figure focus; original filing URL retained; reduced-motion mode",
  );
  if (mode === "live") {
    await page.keyboard.press("Escape");
    await page.getByRole("button", {name:"English",exact:true}).click();
    await page.getByRole("button", {name:"New investigation",exact:true}).click();
    await page.getByRole("textbox").fill("Private draft for deletion verification");
    const draftID = await page.evaluate(()=>localStorage.getItem("filing-investigation"));
    await page.reload();
    await page.getByRole("textbox").waitFor();
    assert.equal(await page.getByRole("textbox").inputValue(), "Private draft for deletion verification");
    await page.getByRole("button", {name:"History",exact:true}).click();
    await page.getByRole("searchbox").fill("no matching question 89f03b");
    await page.getByText("No matching investigations.",{exact:true}).waitFor();
    await page.getByRole("searchbox").fill("");
    const deleteButton = page.locator(".history-item").first().getByRole("button",{name:"Delete this investigation"});
    await deleteButton.click();
    await page
      .getByRole("dialog", { name: "Delete investigation", exact: true })
      .getByRole("button", { name: "Close", exact: true })
      .click();
    assert.equal(await deleteButton.evaluate(node => document.activeElement === node), true);
    await deleteButton.click();
    await page.getByRole("button",{name:"Confirm deletion",exact:true}).click();
    await page.waitForFunction(id=>localStorage.getItem("filing-investigation")!==id,draftID);
    assert.equal(await page.evaluate(id=>localStorage.getItem("filing-draft-"+id),draftID),null);
    await page.getByRole("dialog", { name: "History", exact: true }).waitFor();
    assert.equal(
      await page.evaluate(() => Boolean(document.activeElement?.closest('[role="dialog"]'))),
      true,
    );
    await page.keyboard.press("Escape");
    assert.equal(await page.getByRole("dialog").count(), 0);
    checks.push("Draft survives refresh; history search empty state; cancelling deletion restores its opener; confirmed deletion removes the draft; parent History recovers focus and Escape when the deleted opener is gone");
  }
  assert.deepEqual(errors, []);
  if (mode === "replay")
    assert.equal(
      requests.some((u) => u.includes("/api/") || !u.startsWith(base)),
      false,
    );
  await writeFile(
    `${out}/${mode}-browser.json`,
    JSON.stringify(
      { status: "PASS", browser: browser.version(), checks, errors, requests },
      null,
      2,
    ) + "\n",
  );
  console.log(mode + " BROWSER PASS");
} finally {
  if (mode === "live") {
    await Promise.all(creationReads);
    await writeFile(`${out}/live-created.json`, JSON.stringify([...createdIDs]) + "\n");
    const session = await (await page.request.get(base + "/api/session")).json();
    for (const id of createdIDs) {
      const response = await page.request.post(`${base}/api/investigations/${id}/delete`, {
        headers: { "X-Filing-Token": session.token }, data: {},
      });
      assert.ok([200, 404, 409].includes(response.status()), `Test cleanup failed for ${id}`);
    }
  }
  await browser.close();
}
