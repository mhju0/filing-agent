import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path: string) => JSON.parse(readFileSync(new URL(path, import.meta.url), "utf8"));
const glossary = read("./glossary.json");
const ledger = read("../public/ledger.json");

test("every alias points at a glossary company", () => {
  for (const [alias, id] of Object.entries(glossary.company_aliases)) {
    assert.ok(glossary.companies[id as string], `${alias} -> ${id}`);
  }
});

test("every ledger company and metric has Korean and English names", () => {
  for (const figure of ledger.figures) {
    const id = glossary.company_aliases[figure.company] ?? figure.company;
    assert.equal(glossary.companies[id]?.length, 2, figure.company);
    assert.equal(glossary.metrics[figure.metric]?.length, 2, figure.metric);
  }
});
