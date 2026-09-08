"""Build a bounded, source-checked 15-fact pilot from the captured regulator data."""

from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re

from analyze_coverage import DART, HERE, number, source_bytes, write

METRICS = {
    "revenue": r"^(영업수익|매출액)",
    "operating_income": r"^영업이익",
    "net_income": r"^(연결)?당기순이익(?:\(|$)",
    "net_income_attributable": r"^지배기업",
    "eps": r"^(?!계속).*기본.*주당",
    "eps_diluted": r"^(?!계속).*희석.*주당",
}


def main():
    statements = json.loads((HERE / "dart-statements.json").read_text())
    corpus = json.loads((HERE / "corpus.json").read_text())
    checks = json.loads((HERE / "fact-checks.json").read_text())
    source_checks = json.loads((HERE / "source-checks.json").read_text())
    source_by_path = {r["path"]: r for r in source_checks if "path" in r}
    facts, reviews = [], []
    for check in checks:
        if check["regulator"] == "dart":
            matched = [m for m in check["document_matches"] if re.search(METRICS[check["metric"]], m["row_label"])]
            reviews.append({"fact_id": check["fact_id"], "metric": check["metric"],
                            "selected_rows": matched, "status": "label_rule_unique" if len(matched) == 1 else "ambiguous"})
    assert all(r["status"] == "label_rule_unique" for r in reviews)
    write("dart-label-review.json", reviews)
    for receipt, years in [("20240312000736", [2023, 2022]), ("20240318000844", [2023])]:
        doc = statements[receipt]
        listing = json.loads((HERE / f"sources/dart-list-{receipt}.json").read_text())
        assert listing["status"] == "000" and listing["total_page"] == 1
        filing_metadata = next(r for r in listing["list"] if r["rcept_no"] == receipt and r["corp_code"] == doc["company_code"])
        source_path = f"sources/dart-financials-{doc['company_code']}-2023.json"
        api = json.loads((HERE / source_path).read_text())["list"]
        for year in years:
            column = next(i for i, p in enumerate(doc["periods"]) if p["end"][:4] == str(year)) + 1
            field = "thstrm_amount" if year == 2023 else "frmtrm_amount"
            for metric in ("revenue", "operating_income", "net_income"):
                rows = [(i, r) for i, r in enumerate(doc["rows"]) if len(r) == 4 and re.search(METRICS[metric], r[0]) and number(r[column]) is not None]
                assert len(rows) == 1
                index, row = rows[0]
                value = number(row[column]) * doc["scale"]
                matches = [r for r in api if r["account_id"] == DART[metric] and r["sj_div"] in ("IS", "CIS")
                           and r["corp_code"] == doc["company_code"] and r["rcept_no"] == receipt
                           and r["reprt_code"] == "11011" and r["currency"] == "KRW"
                           and number(r.get(field, "")) == value]
                assert matches
                binding = [f["id"] for f in corpus["data"]["facts"] if f["metric"] == metric and f["fiscal_year"] == year
                           and Decimal(f["value"]) * f["scale"] == value
                           and any(fi["id"] == f["filing_id"] and fi["rcept_no"] == receipt for fi in corpus["data"]["filings"])]
                facts.append({
                    "id": f"dart:{receipt}:{year}:{metric}", "company": "삼성전자" if receipt == "20240312000736" else "NAVER",
                    "company_code": doc["company_code"], "metric": metric, "source_label": row[0],
                    "period": str(year), "period_start": doc["periods"][column-1]["start"],
                    "period_end": doc["periods"][column-1]["end"], "basis": "consolidated",
                    "value": str(value), "currency": "KRW", "scale": 1,
                    "original_value": row[column], "original_unit": doc["original_unit"],
                    "source": {"regulator": "dart", "filing_identity": receipt, "filed_at": f"{filing_metadata['rcept_dt'][:4]}-{filing_metadata['rcept_dt'][4:6]}-{filing_metadata['rcept_dt'][6:8]}",
                        "filing_title": filing_metadata["report_nm"], "filing_metadata_path": f"sources/dart-list-{receipt}.json",
                        "url": f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={receipt}",
                        "link_status": "denial_page_http_200" if receipt == "20240312000736" else "not_rechecked_after_same_host_denials",
                        "section": doc["section"], "section_path": doc["section_path"], "section_sha256": doc["section_sha256"],
                        "row_index": index, "period_column": column, "excerpt_cells": row,
                        "document_path": doc["document_path"], "document_member": doc["member"], "document_sha256": doc["document_sha256"],
                        "api_path": source_path, "api_sha256": source_by_path[source_path]["sha256"],
                        "account_id": matches[0]["account_id"], "account_nm": matches[0]["account_nm"], "api_field": field},
                    "digest_fact_ids": binding,
                    "origin": "verified_digest_fact" if binding else "agent_evidence_supplement_not_ingested_into_digest",
                    "verification": "exact API amount and receipt plus original statement company, row, currency/scale, basis and period",
                })
    for check in checks:
        if check["company"] != "MICROSOFT CORP" or check["period"] not in ("2023-annual", "2024-annual") or check["metric"] not in ("revenue", "operating_income", "net_income"):
            continue
        assert check["api_exact_match"] and check["document_value_match"]
        match = check["document_matches"][0]
        item = match["inline_fact"]
        path = f"sources/filing-{check['filing_identity']}.html.gz"
        raw = source_bytes(HERE / path)
        assert re.search(r"CONSOLIDATED", raw.decode(), re.I)
        facts.append({
            "id": f"sec:{check['filing_identity']}:{check['period']}:{check['metric']}",
            "company": "Microsoft", "company_code": match["context"]["identifier"],
            "metric": check["metric"], "source_label": item.get("row_text", ""),
            "period": check["period"][:4], "period_start": check["period_start"], "period_end": check["period_end"],
            "basis": "consolidated_entity_total", "value": str(Decimal(check["value"]).quantize(Decimal(1))),
            "currency": "USD", "scale": 1, "original_value": item["text"], "original_unit": "USD millions",
            "source": {"regulator": "sec", "filing_identity": check["filing_identity"], "filed_at": check["filed_at"],
                "filing_title": check["filing_title"], "url": check["url"], "link_status": "original_document_downloaded_http_200",
                "document_path": path, "document_sha256": hashlib.sha256(raw).hexdigest(),
                "inline_fact": item, "context": match["context"], "unit_measures": match["unit_measures"],
                "api_path": "sources/sec-companyfacts-0000789019.json.gz", "api_match": check["api_matches"][0],
                "excerpt": item.get("row_text", "")},
            "digest_fact_ids": [check["fact_id"]], "origin": "verified_digest_fact",
            "verification": "exact accession/tag/unit/amount/date match in SEC companyfacts and dimensionless company context in original inline XBRL",
        })
    facts.sort(key=lambda f: f["id"])
    assert len(facts) == 15
    assert Counter(f["origin"] for f in facts) == {"verified_digest_fact": 9, "agent_evidence_supplement_not_ingested_into_digest": 6}
    snapshot = {
        "schema": "coverage-pilot-v1; audit artifact, not the production API contract",
        "upstream_revision": corpus["upstream_revision"], "corpus_sha256": corpus["corpus_sha256"],
        "status": "content_verified_for_local_pilot; public_DART_link_gate_pending",
        "id_policy": "Audit IDs are deterministic source identities, not production ULIDs.",
        "coverage": "Revenue, operating income and as-reported net income; Samsung FY2022/2023, NAVER FY2023, Microsoft FY2023/2024.",
        "limitations": ["Agent-reviewed source bindings, not independent human accounting review.",
            "DART source content was captured through authenticated OpenDART; public viewer accessibility is not verified.",
            "Public URLs are filing-level; internal row/context locators do not promise external cell navigation.",
            "Net income retains its regulator taxonomy; cross-regulator semantic equivalence is not assumed.",
            "Sources are the pinned historical filing occurrences; no exhaustive later-amendment search was performed.",
            "Pilot deliberately contains no R&D metric. Full Samsung report discusses R&D; refusal is about verified scope, not global filing absence."],
        "facts": facts,
    }
    snapshot["snapshot_id"] = "sha256:" + hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
    write("pilot-snapshot.json", snapshot)
    selected = {(f["company"], f["period"], f["metric"]): f for f in facts}
    a = selected[("삼성전자", "2023", "revenue")]
    b = selected[("삼성전자", "2022", "revenue")]
    n = selected[("NAVER", "2023", "revenue")]
    delta = (Decimal(a["value"]) - Decimal(b["value"])) / Decimal(b["value"]) * 100
    write("replay-candidates.json", {
        "snapshot_id": snapshot["snapshot_id"], "status": "verified inputs only; no model runs or replay recording yet",
        "compare": {"question_ko": "삼성전자 2023년 매출액을 2022년과 비교해 줘.", "fact_ids": [a["id"], b["id"]],
                    "absolute_change_krw": str(Decimal(a["value"]) - Decimal(b["value"])),
                    "percentage_change": str(delta.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))},
        "switch": {"questions_ko": ["삼성전자 2023년 매출액은?", "네이버는?"], "fact_ids": [a["id"], n["id"]],
                   "expected_context": {"company": "NAVER", "metric": "revenue", "period": "2023"}},
        "missing": {"question_ko": "삼성전자 2023년 연구개발비는?", "expected_refused": True, "figures": [],
            "reason_code": "outside_verified_metric_scope", "reason_ko": "현재 검증된 연결 손익계산서 범위에는 연구개발비가 없습니다. 공시 전체에 없는 정보라는 뜻은 아닙니다.",
            "trail_scope": "Only the selected verified statement and pilot fact index were checked for answer eligibility.",
            "full_document_contains_rd_discussion": True},
        "us_followup": {"company": "Microsoft", "periods": ["2023", "2024"], "currency": "USD",
            "note": "FY ends June 30; display actual dates. Annual calendar periods include leap-day differences."},
        "negative_controls": ["Apple FY2023 (371 days) versus FY2024 (364 days): withhold automatic percentage pending 52/53-week policy.",
            "Samsung KRW versus Microsoft USD: no cross-currency arithmetic.",
            "A number elsewhere in a source is insufficient without the metric/period binding."]})
    print("PASS: 15 source-bound pilot facts; 9 Digest bindings + 6 explicit Agent supplements; comparison delta", delta.quantize(Decimal("0.01")))


if __name__ == "__main__":
    main()
