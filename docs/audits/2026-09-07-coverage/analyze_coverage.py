"""Offline, corpus-specific evidence audit. This is not a production extractor."""

from collections import Counter, defaultdict
import csv
import datetime as dt
from decimal import Decimal
import hashlib
import gzip
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import zipfile

HERE = Path(__file__).resolve().parent
DART = {
    "revenue": "ifrs-full_Revenue", "operating_income": "dart_OperatingIncomeLoss",
    "net_income": "ifrs-full_ProfitLoss", "net_income_attributable": "ifrs-full_ProfitLossAttributableToOwnersOfParent",
    "eps": "ifrs-full_BasicEarningsLossPerShare", "eps_diluted": "ifrs-full_DilutedEarningsLossPerShare",
}
SEC = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "operating_income": ["OperatingIncomeLoss"], "net_income": ["NetIncomeLoss"],
    "eps": ["EarningsPerShareBasic"], "eps_diluted": ["EarningsPerShareDiluted"],
}


def source_bytes(path):
    if not path.exists():
        path = path.with_suffix(path.suffix + ".gz")
    return gzip.decompress(path.read_bytes()) if path.suffix == ".gz" else path.read_bytes()


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value))).strip()


def number(value):
    value = value.replace(",", "").replace(" ", "").replace("−", "-")
    if value.startswith("(") and value.endswith(")"):
        value = "-" + value[1:-1]
    if not re.fullmatch(r"-?\d+(\.\d+)?", value):
        return None
    return Decimal(value)


def write(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n")


class InlineFacts(HTMLParser):
    def __init__(self, document):
        super().__init__(convert_charrefs=True)
        self.contexts, self.units, self.facts = {}, {}, []
        self.context = self.unit = self.fact = self.field = None
        self.rows = []
        self.feed(document)

    def handle_starttag(self, tag, attributes):
        attrs, local = dict(attributes), tag.split(":")[-1]
        if local == "context":
            self.context = {"id": attrs["id"], "dimensional": False}
        if local in ("explicitmember", "typedmember", "segment", "scenario") and self.context is not None:
            self.context["dimensional"] = True
        if self.context is not None and local in ("identifier", "startdate", "enddate", "instant"):
            self.field = local
        if local == "unit":
            self.unit = {"id": attrs["id"], "measures": []}
        if self.unit is not None and local == "measure":
            self.field = "measure"
        if tag == "tr":
            self.rows.append({"text": [], "facts": []})
        if tag == "ix:nonfraction":
            self.fact = {**attrs, "text": ""}

    def handle_data(self, data):
        if self.context is not None and self.field in ("identifier", "startdate", "enddate", "instant"):
            self.context[self.field] = self.context.get(self.field, "") + data.strip()
        if self.unit is not None and self.field == "measure" and data.strip():
            self.unit["measures"].append(data.strip())
        if self.fact is not None:
            self.fact["text"] += data
        if self.rows:
            self.rows[-1]["text"].append(data)

    def handle_endtag(self, tag):
        local = tag.split(":")[-1]
        if local in ("identifier", "startdate", "enddate", "instant", "measure"):
            self.field = None
        if local == "context" and self.context is not None:
            self.contexts[self.context["id"]] = self.context
            self.context = None
        if local == "unit" and self.unit is not None:
            self.units[self.unit["id"]] = self.unit["measures"]
            self.unit = None
        if tag == "ix:nonfraction" and self.fact is not None:
            self.facts.append(self.fact)
            if self.rows:
                self.rows[-1]["facts"].append(self.fact)
            self.fact = None
        if tag == "tr" and self.rows:
            row = self.rows.pop()
            for fact in row["facts"]:
                fact["row_text"] = " ".join(" ".join(row["text"]).split())


def dart_document(receipt):
    filename = f"sources/dart-document-{receipt}.zip"
    with zipfile.ZipFile(HERE / filename) as archive:
        member = receipt + ".xml"
        raw = archive.read(member)
    document = raw.decode("utf-8")
    headings = list(re.finditer(r"<TITLE\b[^>]*>(.*?)</TITLE>", document, re.S))
    heading = next(h for h in headings if re.match(r"2-2\. 연결", clean(h[1])))
    end = next(h.start() for h in headings if h.start() > heading.start())
    section = document[heading.start():end]
    rows = [[clean(c) for c in re.findall(r"<(?:TD|TE|TH)\b[^>]*>(.*?)</(?:TD|TE|TH)>", r, re.S)]
            for r in re.findall(r"<TR\b[^>]*>(.*?)</TR>", section, re.S)]
    ranges = re.findall(r"(\d{4}\.\d{2}\.\d{2}) 부터 (\d{4}\.\d{2}\.\d{2}) 까지", clean(section))
    unit = re.search(r"\(단위\s*:\s*([^)]*)\)", clean(section))[1].strip()
    scale = {"원": 1, "천원": 1000, "백만원": 1000000}[unit]
    corp = re.search(r'<COMPANY-NAME\b[^>]*AREGCIK="(\d+)"[^>]*>(.*?)</COMPANY-NAME>', document)
    result = {
        "receipt": receipt, "document_path": filename, "member": member,
        "document_sha256": hashlib.sha256(raw).hexdigest(),
        "company_code": corp[1], "company_name": clean(corp[2]),
        "section": clean(heading[1]), "original_unit": unit, "scale": scale,
        "periods": [{"start": a.replace(".", "-"), "end": b.replace(".", "-")} for a, b in ranges],
        "rows": rows, "section_text": clean(section),
        "section_character_range": [heading.start(), end],
        "section_sha256": hashlib.sha256(section.encode()).hexdigest(),
        "extraction": "Exact bounded section; whitespace-normalized cell text. XML document retained unchanged; not parsed as strict XML because regulator body is not well-formed XML.",
    }
    (HERE / "excerpts").mkdir(exist_ok=True)
    (HERE / "excerpts" / f"{receipt}.txt").write_text(section)
    result["section_path"] = f"excerpts/{receipt}.txt"
    return result


def main():
    capture = json.loads((HERE / "corpus.json").read_text())
    data = capture["data"]
    companies = {c["id"]: c for c in data["companies"]}
    filings = {f["id"]: f for f in data["filings"]}
    source_checks = json.loads((HERE / "source-checks.json").read_text())
    for check in source_checks:
        if "path" in check:
            assert hashlib.sha256(source_bytes(HERE / check["path"])).hexdigest() == check["sha256"]
    api_dart, docs_dart, api_sec, docs_sec = {}, {}, {}, {}
    for path in (HERE / "sources").glob("dart-financials-*.json"):
        payload = json.loads(path.read_text())
        assert payload["status"] == "000"
        rows = payload["list"]
        receipt = rows[0]["rcept_no"]
        assert {r["rcept_no"] for r in rows} == {receipt}
        api_dart[receipt] = {"rows": rows, "path": str(path.relative_to(HERE))}
        docs_dart[receipt] = dart_document(receipt)
    for c in data["companies"]:
        if c["source"] == "sec":
            path = HERE / "sources" / f"sec-companyfacts-{c['sec_cik']}.json"
            api_sec[c["id"]] = json.loads(source_bytes(path), parse_float=Decimal)
    for f in data["filings"]:
        if f["source"] == "sec":
            path = HERE / "sources" / f"filing-{f['sec_accession_no']}.html"
            docs_sec[f["id"]] = InlineFacts(source_bytes(path).decode())

    checks = []
    for fact in data["facts"]:
        company, filing = companies[fact["company_id"]], filings[fact["filing_id"]]
        result = {"fact_id": fact["id"], "company": company["name"], "company_id": company["id"],
                  "metric": fact["metric"], "period": fact["period"], "value": fact["value"],
                  "currency": fact["currency"], "unit": fact["unit"], "scale": fact["scale"],
                  "filing_id": filing["id"], "filing_period": filing["period"], "filing_title": filing["title"],
                  "filed_at": filing["filed_at"], "url": filing["url"],
                  "regulator": company["source"], "api_matches": [], "document_matches": []}
        if company["source"] == "dart":
            receipt = filing["rcept_no"]
            doc = docs_dart[receipt]
            assert doc["company_code"] == company["dart_corp_code"]
            result.update(filing_identity=receipt, public_link_status="denial_page_http_200", basis="consolidated")
            for row in api_dart[receipt]["rows"]:
                if row["account_id"] != DART[fact["metric"]] or row["sj_div"] not in ("IS", "CIS"):
                    continue
                offset = int(row["bsns_year"]) - fact["fiscal_year"]
                if offset not in (0, 1, 2):
                    continue
                field = ["thstrm_amount", "frmtrm_amount", "bfefrmtrm_amount"][offset]
                if number(row.get(field, "")) == Decimal(fact["value"]) * fact["scale"] and row["currency"] == fact["currency"]:
                    result["api_matches"].append({"path": api_dart[receipt]["path"], "account_id": row["account_id"],
                        "account_nm": row["account_nm"], "statement": row["sj_div"], "field": field, "ord": row["ord"]})
            period_index = next(i for i, p in enumerate(doc["periods"]) if p["end"][:4] == str(fact["fiscal_year"]))
            result.update(period_start=doc["periods"][period_index]["start"], period_end=doc["periods"][period_index]["end"])
            for index, row in enumerate(doc["rows"]):
                if len(row) != 4:
                    continue
                amount = number(row[period_index + 1])
                scale = 1 if fact["metric"].startswith("eps") else doc["scale"]
                if amount is not None and amount * scale == Decimal(fact["value"]) * fact["scale"]:
                    result["document_matches"].append({"section_path": doc["section_path"], "row_index": index,
                        "row_label": row[0], "row": row, "period_column": period_index + 1,
                        "source_unit": "원/주" if fact["metric"].startswith("eps") else doc["original_unit"],
                        "status": "value_and_period_candidate_requires_label_review"})
        else:
            accession = filing["sec_accession_no"]
            source = api_sec[company["id"]]
            assert str(source["cik"]).zfill(10) == company["sec_cik"]
            doc = docs_sec[filing["id"]]
            result.update(filing_identity=accession, public_link_status="document_downloaded_http_200")
            for tag in SEC.get(fact["metric"], []):
                unit = "USD/shares" if fact["metric"].startswith("eps") else "USD"
                for entry in source["facts"]["us-gaap"].get(tag, {}).get("units", {}).get(unit, []):
                    if entry.get("accn") != accession or entry.get("form") != "10-K" or not entry.get("start"):
                        continue
                    days = (dt.date.fromisoformat(entry["end"]) - dt.date.fromisoformat(entry["start"])).days + 1
                    if not (300 <= days <= 380) or entry["end"][:4] != str(fact["fiscal_year"]):
                        continue
                    if Decimal(entry["val"]) == Decimal(fact["value"]) * fact["scale"]:
                        result["api_matches"].append({"tag": tag, "unit": unit, "entry": entry, "days": days})
            for match in result["api_matches"]:
                for item in doc.facts:
                    ctx = doc.contexts.get(item.get("contextref"), {})
                    if item.get("name") != "us-gaap:" + match["tag"] or ctx.get("dimensional"):
                        continue
                    if ctx.get("startdate") != match["entry"]["start"] or ctx.get("enddate") != match["entry"]["end"]:
                        continue
                    if ctx.get("identifier", "").zfill(10) != company["sec_cik"]:
                        continue
                    amount = number(item["text"])
                    if amount is None:
                        continue
                    amount *= Decimal(10) ** int(item.get("scale", 0))
                    if item.get("sign") == "-":
                        amount = -amount
                    measures = doc.units.get(item.get("unitref"), [])
                    expected_measures = {"iso4217:USD", "xbrli:shares"} if fact["metric"].startswith("eps") else {"iso4217:USD"}
                    if amount == Decimal(fact["value"]) * fact["scale"] and set(measures) == expected_measures:
                        result["document_matches"].append({"context": ctx, "inline_fact": item, "unit_measures": measures})
            if result["document_matches"]:
                ctx = result["document_matches"][0]["context"]
                result.update(period_start=ctx["startdate"], period_end=ctx["enddate"], basis="entity_total_dimensionless_context")
        result["api_exact_match"] = bool(result["api_matches"])
        result["document_value_match"] = bool(result["document_matches"])
        result["status"] = "candidate_source_supported" if result["api_matches"] and result["document_matches"] else "needs_review"
        checks.append(result)
    write("fact-checks.json", checks)
    columns = ["company", "regulator", "metric", "period", "period_start", "period_end", "value", "currency", "unit", "scale", "basis", "filing_identity", "filing_title", "filing_period", "filed_at", "url", "api_exact_match", "document_value_match", "public_link_status", "status"]
    with (HERE / "coverage.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted(checks, key=lambda c: (c["company"], c["period"], c["metric"])))
    write("dart-statements.json", docs_dart)
    summary = {"captured_at": capture["captured_at"], "upstream_revision": capture["upstream_revision"],
               "corpus_sha256": capture["corpus_sha256"], "counts": capture["counts"],
               "api_exact_matches": sum(c["api_exact_match"] for c in checks),
               "document_value_candidates": sum(c["document_value_match"] for c in checks),
               "statuses": dict(Counter(c["status"] for c in checks)),
               "companies": []}
    for company in sorted(data["companies"], key=lambda c: c["name"]):
        by_period = defaultdict(list)
        for check in checks:
            if check["company_id"] == company["id"]:
                by_period[check["period"]].append(check["metric"])
        summary["companies"].append({"name": company["name"], "regulator": company["source"],
                                     "periods": {p: sorted(m) for p, m in sorted(by_period.items())}})
    write("coverage.json", summary)
    print(json.dumps({k: v for k, v in summary.items() if k != "companies"}, indent=2))
    for check in checks:
        if check["status"] == "needs_review":
            print(check["company"], check["period"], check["metric"], check["value"], "api", check["api_exact_match"], "document", check["document_value_match"])


if __name__ == "__main__":
    main()
