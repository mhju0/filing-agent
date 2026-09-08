"""Verify saved evidence offline, including rejection of corrupted pilot bindings."""

import copy
from decimal import Decimal
import hashlib
import json

from analyze_coverage import HERE, DART, SEC, InlineFacts, number, source_bytes, write


def main():
    corpus = json.loads((HERE / "corpus.json").read_text())
    canonical = json.dumps(corpus["data"], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    assert hashlib.sha256(canonical).hexdigest() == corpus["corpus_sha256"]
    assert corpus["transaction"]["read_only"] == "on"
    assert corpus["upstream_status_before"] == corpus["upstream_status_after"]
    sources = json.loads((HERE / "source-checks.json").read_text())
    for source in sources:
        raw = source_bytes(HERE / source["path"])
        assert len(raw) == source["bytes"]
        assert hashlib.sha256(raw).hexdigest() == source["sha256"]
    pilot = json.loads((HERE / "pilot-snapshot.json").read_text())
    without_id = {k: v for k, v in pilot.items() if k != "snapshot_id"}
    assert pilot["snapshot_id"] == "sha256:" + hashlib.sha256(json.dumps(without_id, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    statements = json.loads((HERE / "dart-statements.json").read_text())
    parsed = {}

    def verify_fact(fact):
        source = fact["source"]
        value = Decimal(fact["value"])
        assert fact["period_start"] < fact["period_end"] and fact["period"] == fact["period_end"][:4]
        if source["regulator"] == "dart":
            doc = statements[source["filing_identity"]]
            assert fact["company_code"] == doc["company_code"]
            assert source["account_id"] == DART[fact["metric"]]
            assert source["section_sha256"] == hashlib.sha256((HERE / source["section_path"]).read_bytes()).hexdigest()
            row = doc["rows"][source["row_index"]]
            assert row == source["excerpt_cells"] and row[0] == fact["source_label"]
            assert value == number(row[source["period_column"]]) * doc["scale"]
            period = doc["periods"][source["period_column"] - 1]
            assert (period["start"], period["end"]) == (fact["period_start"], fact["period_end"])
            api = json.loads((HERE / source["api_path"]).read_text())["list"]
            assert any(r["rcept_no"] == source["filing_identity"] and r["corp_code"] == fact["company_code"]
                       and r["account_id"] == source["account_id"] and r["sj_div"] in ("IS", "CIS")
                       and r["currency"] == fact["currency"] and number(r.get(source["api_field"], "")) == value for r in api)
        else:
            path = source["document_path"]
            if path not in parsed:
                parsed[path] = InlineFacts(source_bytes(HERE / path).decode())
            doc = parsed[path]
            item, ctx = source["inline_fact"], source["context"]
            assert item in doc.facts and doc.contexts[item["contextref"]] == ctx
            assert not ctx["dimensional"] and ctx["identifier"] == fact["company_code"]
            assert ctx["startdate"] == fact["period_start"] and ctx["enddate"] == fact["period_end"]
            assert item["name"] in {"us-gaap:" + t for t in SEC[fact["metric"]]}
            assert value == number(item["text"]) * Decimal(10) ** int(item.get("scale", 0)) * (-1 if item.get("sign") == "-" else 1)
            assert doc.units[item["unitref"]] == ["iso4217:USD"] and fact["currency"] == "USD"
            api = json.loads(source_bytes(HERE / source["api_path"]), parse_float=Decimal)
            match = source["api_match"]
            assert match["entry"] in api["facts"]["us-gaap"][match["tag"]]["units"]["USD"]
            assert match["entry"]["accn"] == source["filing_identity"] and Decimal(match["entry"]["val"]) == value

    for fact in pilot["facts"]:
        verify_fact(fact)
    base = next(f for f in pilot["facts"] if f["company"] == "삼성전자" and f["period"] == "2023" and f["metric"] == "revenue")
    mutations = [lambda f: f.update(value=str(Decimal(f["value"]) + 1)),
                 lambda f: f["source"].update(period_column=2),
                 lambda f: f["source"].update(account_id="ifrs-full_ProfitLoss")]
    for mutate in mutations:
        changed = copy.deepcopy(base)
        mutate(changed)
        try:
            verify_fact(changed)
        except AssertionError:
            pass
        else:
            raise AssertionError("Corrupted financial binding was accepted")
    checks = json.loads((HERE / "fact-checks.json").read_text())
    assert len(checks) == 86 and all(c["api_exact_match"] and c["document_value_match"] for c in checks)
    assert len(json.loads((HERE / "dart-label-review.json").read_text())) == 46
    scenarios = json.loads((HERE / "replay-candidates.json").read_text())
    assert scenarios["snapshot_id"] == pilot["snapshot_id"]
    assert scenarios["compare"]["percentage_change"] == "-14.33"
    assert scenarios["missing"]["expected_refused"] and not scenarios["missing"]["figures"]
    report = {"result": "PASS", "source_payload_hashes": len(sources), "corpus_fingerprint": "matched",
              "stored_facts_matched_to_regulator_api": 86, "original_document_value_candidates": 86,
              "dart_labels_disambiguated": 46, "pilot_fact_bindings_verified": len(pilot["facts"]),
              "corrupted_bindings_rejected": ["value changed", "source period column changed", "account taxonomy changed"],
              "scope": "Offline evidence audit only; no model, public replay, live application or browser-link release pass."}
    write("verification.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
