// Every displayed amount and percentage goes through this module.
// Values arrive as exact decimal strings; BigInt keeps them exact.
export type Lang = "ko" | "en";

export const MINUS = "−";

export function exact(value: string) {
  const negative = value.startsWith("-");
  const [a, b] = value.replace(/^-/, "").split(".");
  return (negative ? MINUS : "") + BigInt(a).toLocaleString("en-US") + (b ? "." + b : "");
}

// Trillions of won, billions of dollars, one decimal. "≈" marks rounding.
export function compact(value: string, currency: string, lang: Lang) {
  const divisor = currency === "KRW" ? 1_000_000_000_000n : 1_000_000_000n;
  const v = BigInt(value.split(".")[0]);
  const abs = v < 0n ? -v : v;
  const tenths = (abs * 10n + divisor / 2n) / divisor;
  const approx = (abs * 10n) % divisor === 0n ? "" : "≈ ";
  const number = (v < 0n ? MINUS : "") + (tenths / 10n).toLocaleString("en-US") + "." + (tenths % 10n);
  if (currency === "KRW") return approx + number + (lang === "ko" ? "조 원" : "tn KRW");
  if (lang === "en") return approx + (v < 0n ? MINUS : "") + "$" + number.replace(MINUS, "") + "bn";
  // Korean readers count dollars in 억 달러; round to whole 억.
  const eok = (abs + 50_000_000n) / 100_000_000n;
  return (abs % 100_000_000n ? "≈ " : "") + (v < 0n ? MINUS : "") + eok.toLocaleString("en-US") + "억 달러";
}

// Korean readers check large won amounts in 조/억 units; this is the exact
// value restated, not rounded.
export function koreanUnits(value: string) {
  const v = BigInt(value.split(".")[0]);
  const abs = v < 0n ? -v : v;
  const jo = abs / 1_000_000_000_000n;
  const eok = (abs % 1_000_000_000_000n) / 100_000_000n;
  const man = (abs % 100_000_000n) / 10_000n;
  const rest = abs % 10_000n;
  const parts = [];
  if (jo) parts.push(jo.toLocaleString("en-US") + "조");
  if (eok) parts.push(eok.toLocaleString("en-US") + "억");
  if (man) parts.push(man.toLocaleString("en-US") + "만");
  if (rest || !parts.length) parts.push(rest.toLocaleString("en-US"));
  return (v < 0n ? MINUS : "") + parts.join(" ") + " 원";
}

// Signed percentage from a decimal string such as "-14.33".
export function signedPercent(value: string) {
  if (value.startsWith("-")) return MINUS + value.slice(1) + "%";
  return (/^0(\.0+)?$/.test(value) ? "" : "+") + value + "%";
}

function scaled(value: string, places: number) {
  const [a, b = ""] = value.split(".");
  return BigInt(a + b.padEnd(places, "0").slice(0, places)) * (a.startsWith("-") && !BigInt(a) ? -1n : 1n);
}

// numerator / denominator × 100, rounded half away from zero, matching the
// Decimal ROUND_HALF_UP used by slice/financial.py.
export function ratio(numerator: string, denominator: string, decimals = 1) {
  const n = scaled(numerator, 6);
  const d = scaled(denominator, 6);
  if (d === 0n) return null;
  const negative = (n < 0n) !== (d < 0n) && n !== 0n;
  const an = n < 0n ? -n : n;
  const ad = d < 0n ? -d : d;
  const unit = 10n ** BigInt(decimals);
  const q = (an * 100n * unit * 2n + ad) / (ad * 2n);
  const whole = (q / unit).toString();
  const frac = decimals ? "." + (q % unit).toString().padStart(decimals, "0") : "";
  return (negative ? "-" : "") + whole + frac;
}

export function change(current: string, prior: string) {
  const delta = (BigInt(current.split(".")[0]) - BigInt(prior.split(".")[0])).toString();
  return { absolute: delta, percent: ratio(delta, prior, 2) };
}
