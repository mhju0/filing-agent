import { chromium } from "playwright";
import AxeBuilder from "@axe-core/playwright";
import assert from "node:assert/strict";
import { writeFile, mkdir, rm } from "node:fs/promises";

const base = process.env.DESIGN_URL || "http://127.0.0.1:4174";
const browser = await chromium.launch({ channel: "chrome", headless: true });
const report = {
  date: new Date().toISOString(),
  browser: browser.version(),
  pages: [],
  externalRequests: [],
};
await mkdir("screenshots", { recursive: true });
const context = await browser.newContext({
  viewport: { width: 1440, height: 1200 },
  colorScheme: "light",
  reducedMotion: "reduce",
});
await context.route("**/*", (route) => {
  if (new URL(route.request().url()).origin !== new URL(base).origin) {
    report.externalRequests.push(route.request().url());
    return route.abort();
  }
  return route.continue();
});
const page = await context.newPage();
const errors = [];
page.on("pageerror", (error) => errors.push(error.message));
page.on("console", (message) => {
  if (message.type() === "error") errors.push(message.text());
});
const overflowing = () =>
  page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
const reset = async (variant, lang = "ko", theme = "light") => {
  await page.goto(`${base}/${variant}.html`);
  await page.evaluate(
    ({ lang, theme }) => {
      localStorage.setItem("filing-design-language", lang);
      localStorage.setItem("filing-design-theme", theme);
    },
    { lang, theme },
  );
  await page.reload();
  await page.evaluate(() => document.fonts.ready);
};

try {
  for (const variant of ["a", "b", "c"]) {
    const checks = [];
    await page.setViewportSize({ width: 1440, height: 1200 });
    await reset(variant);
    await page
      .getByRole("heading", { name: "삼성전자 연간 매출 비교" })
      .waitFor();
    assert.equal(await page.locator(".evidence").count(), 1);
    assert.equal(
      await page
        .locator(".selected-evidence")
        .innerText()
        .then((text) => text.includes("2023")),
      true,
    );
    assert.equal(await page.locator(".trail li").count(), 5);
    assert.equal(
      await page.locator(".context-chip.changed").innerText(),
      "2023✓",
    );
    await page.screenshot({ path: `screenshots/${variant}-desktop.png` });
    checks.push(
      "Korean/light desktop, selected 2023 evidence, confirmed chips, five illustrative completed stages",
    );

    const calc = page.getByRole("button", { name: "계산됨", exact: true });
    await calc.focus();
    await page.keyboard.press("Enter");
    assert.equal(await calc.getAttribute("aria-expanded"), "true");
    assert.equal(
      await calc.evaluate((element) => element === document.activeElement),
      true,
    );
    assert.match(await page.locator("#formula").innerText(), /−14\.33/);
    assert.equal(await page.locator("#formula .figure-button").count(), 2);
    await page.locator("#formula .figure-button").nth(1).click();
    assert.match(
      await page.locator(".selected-evidence").innerText(),
      /302\.2조원.*2022/s,
    );
    await page.getByRole("button", { name: "공시 근거 닫기" }).click();
    assert.equal(await page.locator(".evidence").count(), 0);
    await page.waitForFunction(
      () =>
        document.activeElement ===
        document.querySelectorAll("#formula .figure-button")[1],
    );
    assert.equal(
      await page
        .locator("#formula .figure-button")
        .nth(1)
        .evaluate((element) => element === document.activeElement),
      true,
    );
    await page.locator("#formula .figure-button").first().click();
    await page.getByRole("button", { name: "번역 보기" }).click();
    assert.match(await page.locator(".translation").innerText(), /258,935,494/);
    await page.locator(".explanation summary").click();
    assert.equal(await page.locator(".explanation").getAttribute("open"), "");
    await page.screenshot({ path: `screenshots/${variant}-formula.png` });
    checks.push(
      "Keyboard formula toggle preserves focus; both operands select sources; evidence close returns focus; explanation and labeled translation open",
    );

    await page.getByRole("button", { name: "기록", exact: true }).click();
    await page.getByRole("button", { name: /이 조사 열기/ }).click();
    assert.equal(await page.locator("dialog[open]").count(), 0);
    await page.getByRole("button", { name: "새 조사", exact: true }).click();
    await page.getByRole("button", { name: "질문 작성하기" }).click();
    await page.getByRole("textbox").fill("영업이익도 비교해 줘");
    await page.getByRole("button", { name: "질문 보내기" }).click();
    assert.match(await page.getByRole("alert").innerText(), /정적 시안/);
    assert.equal(
      await page.getByRole("textbox").inputValue(),
      "영업이익도 비교해 줘",
    );
    await page.getByRole("textbox").fill("한글");
    await page
      .getByRole("textbox")
      .dispatchEvent("keydown", { key: "Enter", isComposing: true });
    assert.equal(await page.getByRole("alert").count(), 0);
    await page.getByRole("button", { name: "삼성전자", exact: true }).click();
    await page.keyboard.press("Escape");
    checks.push(
      "History reopen; new draft; honest static-submit error retains draft; IME Enter does not submit; context dialog dismisses",
    );

    await reset(variant);
    for (const lang of ["ko", "en"]) {
      for (const theme of ["light", "dark"]) {
        if (variant !== "b")
          await page.getByRole("button", { name: /^(설정|Settings)$/ }).click();
        await page
          .getByRole("button", {
            name: lang === "ko" ? "한국어" : "English",
            exact: true,
          })
          .click();
        if (variant === "b") {
          if ((await page.locator("html").getAttribute("data-theme")) !== theme)
            await page.locator(".theme-toggle").click();
          assert.equal(
            await page
              .getByRole("button", { name: /^(설정|Settings)$/ })
              .count(),
            0,
          );
        } else {
          await page
            .getByRole("button", {
              name: theme === "dark" ? /^(다크|Dark)$/ : /^(라이트|Light)$/,
            })
            .click();
          await page.keyboard.press("Escape");
        }
        assert.equal(await page.locator("html").getAttribute("lang"), lang);
        assert.equal(
          await page.locator("html").getAttribute("data-theme"),
          theme,
        );
        const audit = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        const violations = audit.violations.map((v) => ({
          id: v.id,
          impact: v.impact,
          nodes: v.nodes.map((n) => ({
            target: n.target,
            summary: n.failureSummary,
          })),
        }));
        if (violations.length)
          report.pages.push({ variant, lang, theme, violations });
        assert.equal(violations.length, 0, JSON.stringify(violations, null, 2));
        assert.equal(
          await overflowing(),
          false,
          `${variant}/${lang}/${theme} overflows`,
        );
        if (lang === "en" && theme === "dark")
          await page.screenshot({
            path: `screenshots/${variant}-english-dark.png`,
          });
      }
    }
    checks.push(
      "Working language/theme controls; automated accessibility audit in both languages and both themes; English/dark capture",
    );

    for (const width of [375, 390, 768, 1024, 1280]) {
      await page.setViewportSize({ width, height: width < 761 ? 844 : 1000 });
      await reset(variant);
      assert.equal(
        await overflowing(),
        false,
        `${variant} overflows at ${width}`,
      );
      if (width === 390) {
        if (variant === "b") {
          assert.equal(await page.locator(".evidence").count(), 0);
          await page
            .getByRole("button", { name: "English", exact: true })
            .click();
          await page
            .getByRole("button", { name: "한국어", exact: true })
            .click();
          await page.locator(".ledger-heroes .figure-button").first().click();
        }
        const bounds = await page.locator(".evidence").boundingBox();
        assert.ok(
          Math.abs(bounds.height - 844 * (variant === "b" ? 1 : 0.4)) < 3,
        );
        await page.screenshot({ path: `screenshots/${variant}-mobile.png` });
        const mobileAudit = await new AxeBuilder({ page })
          .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
          .analyze();
        assert.equal(
          mobileAudit.violations.length,
          0,
          JSON.stringify(
            mobileAudit.violations.map((v) => ({
              id: v.id,
              nodes: v.nodes.map((n) => n.failureSummary),
            })),
            null,
            2,
          ),
        );
        if (variant !== "b") {
          await page
            .getByRole("button", { name: "펼치기", exact: true })
            .click();
          assert.ok(
            (await page.locator(".evidence").boundingBox()).height > 800,
          );
          await page.getByRole("button", { name: "접기", exact: true }).click();
          const handle = await page.locator(".sheet-grip").boundingBox();
          await page.mouse.move(handle.x + handle.width / 2, handle.y + 8);
          await page.mouse.down();
          await page.mouse.move(handle.x + handle.width / 2, handle.y - 85);
          await page.mouse.up();
        } else {
          assert.equal(
            await page.locator(".sheet-grip, .sheet-expand").count(),
            0,
          );
        }
        assert.ok((await page.locator(".evidence").boundingBox()).height > 800);
        await page.keyboard.press("Escape");
        assert.equal(await page.locator(".evidence").count(), 0);
        if (variant === "b") {
          assert.equal(
            await page
              .locator(".ledger-heroes .figure-button")
              .first()
              .evaluate((el) => el === document.activeElement),
            true,
          );
        }
        assert.equal(await page.getByRole("textbox").isVisible(), true);
        await page.screenshot({
          path: `screenshots/${variant}-mobile-conversation.png`,
        });
      }
    }
    checks.push(
      variant === "b"
        ? "No overflow at 375/390/768/1024/1280; mobile starts in conversation; visible language controls; full-height evidence without drag/detents; Escape restores figure focus"
        : "No document overflow at 375/390/768/1024/1280; 390px peek at 40%; expand/collapse/drag/Escape; composer reachable after sheet close",
    );
    await page.setViewportSize({ width: 390, height: 844 });
    await reset(variant, "en", "dark");
    assert.equal(await overflowing(), false);
    if (variant === "b")
      await page.locator(".ledger-heroes .figure-button").first().click();
    else
      await page.getByRole("button", { name: "Expand", exact: true }).click();
    const englishMobileAudit = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    assert.equal(
      englishMobileAudit.violations.length,
      0,
      JSON.stringify(englishMobileAudit.violations.map((v) => v.id)),
    );
    await page
      .getByRole("button", { name: "Filing evidence Close", exact: true })
      .click();
    assert.equal(await overflowing(), false);
    await page.screenshot({
      path: `screenshots/${variant}-mobile-english-dark.png`,
    });
    checks.push(
      "English/dark mobile expanded evidence passes axe; conversation reflows without document overflow",
    );
    report.pages.push({ variant, checks });
  }
  assert.equal(report.externalRequests.length, 0);
  assert.equal(errors.length, 0, errors.join("\n"));
  report.result = "PASS";
  await rm("screenshots/verification-failure.png", { force: true });
  report.consoleErrors = errors;
  console.log(
    "PASS: all three alternatives, bilingual/themes, interactions, responsive sheets, axe audits, zero external requests.",
  );
} catch (error) {
  report.result = "FAIL";
  report.error = error.message;
  await page.screenshot({ path: "screenshots/verification-failure.png" });
  throw error;
} finally {
  await writeFile("verification.json", JSON.stringify(report, null, 2) + "\n");
  await browser.close();
}
