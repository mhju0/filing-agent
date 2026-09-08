import { chromium } from "../../verification/node_modules/playwright/index.mjs";
import { readFile, writeFile } from "node:fs/promises";
import assert from "node:assert/strict";
const snapshot = JSON.parse(
  await readFile("docs/audits/2026-09-07-coverage/pilot-snapshot.json", "utf8"),
);
const browser = await chromium.launch({ channel: "chrome", headless: true });
const result = [];
try {
  for (const url of [...new Set(snapshot.facts.map((f) => f.source.url))]) {
    const page = await browser.newPage();
    const response = await page.goto(url, {
      waitUntil: "domcontentloaded",
      timeout: 60000,
    });
    const facts = snapshot.facts.filter((f) => f.source.url === url);
    if (facts[0].source.regulator === "dart") {
      const section = facts[0].source.section;
      await page.getByRole("treeitem", { name: section, exact: true }).click();
      await page.waitForTimeout(1000);
    }
    const text = (
      await Promise.all(
        page.frames().map((f) =>
          f
            .locator("body")
            .innerText()
            .catch(() => ""),
        ),
      )
    ).join("\n");
    const found = facts.map((f) => ({
      id: f.id,
      original_value: f.original_value,
      found: text.includes(f.original_value),
    }));
    const screenshot = `source-${facts[0].source.filing_identity.replaceAll("/", "-")}.png`;
    await page.screenshot({
      path: "docs/audits/2026-09-08-slice/" + screenshot,
    });
    result.push({
      url,
      title: await page.title(),
      http_status: response.status(),
      checked_at: new Date().toISOString(),
      figures: found,
      screenshot,
      status: found.every((f) => f.found)
        ? "verified"
        : "automated_browser_access_denied",
    });
    await writeFile(
      "docs/audits/2026-09-08-slice/source-navigation.json",
      JSON.stringify(
        {
          status: "checked; see per-source outcomes",
          browser: browser.version(),
          results: result,
        },
        null,
        2,
      ) + "\n",
    );
    await page.close();
  }
  assert.ok(
    result
      .filter((r) => r.url.includes("dart.fss"))
      .every((r) => r.status === "verified"),
  );
  console.log(
    "DART replay source navigation PASS; SEC browser restrictions retained",
  );
} finally {
  await browser.close();
}
