import { test } from "node:test";
import assert from "node:assert/strict";
import { change, compact, exact, koreanUnits, ratio, signedPercent } from "./format.ts";

test("exact keeps every digit with separators and a true minus", () => {
  assert.equal(exact("258935494000000"), "258,935,494,000,000");
  assert.equal(exact("-43296266000000"), "−43,296,266,000,000");
});

test("compact rounds to one decimal and marks rounding", () => {
  assert.equal(compact("258935494000000", "KRW", "ko"), "≈ 258.9조 원");
  assert.equal(compact("258935494000000", "KRW", "en"), "≈ 258.9tn KRW");
  assert.equal(compact("245122000000", "USD", "en"), "≈ $245.1bn");
  assert.equal(compact("245122000000", "USD", "ko"), "≈ 2,451억 달러");
  assert.equal(compact("88000000000", "USD", "en"), "$88.0bn");
});

test("Korean units restate the exact won amount", () => {
  assert.equal(koreanUnits("258935494000000"), "258조 9,354억 9,400만 원");
  assert.equal(koreanUnits("6566976000000"), "6조 5,669억 7,600만 원");
});

test("signed percent uses a true minus and an explicit plus", () => {
  assert.equal(signedPercent("-14.33"), "−14.33%");
  assert.equal(signedPercent("15.67"), "+15.67%");
  assert.equal(signedPercent("0.00"), "0.00%");
});

test("ratio rounds half away from zero like Decimal ROUND_HALF_UP", () => {
  assert.equal(ratio("6566976000000", "258935494000000"), "2.5");
  assert.equal(ratio("1", "8", 2), "12.50");
  assert.equal(ratio("1", "800", 1), "0.1");
  assert.equal(ratio("-1", "8", 1), "-12.5");
  assert.equal(ratio("1", "0"), null);
});

test("change matches the policy's recorded Samsung revenue comparison", () => {
  assert.deepEqual(change("258935494000000", "302231360000000"), { absolute: "-43295866000000", percent: "-14.33" });
});
