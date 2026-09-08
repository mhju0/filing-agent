"""Snapshot validation and the measured intent/financial policy boundary."""

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))
from intent import OPTIONS, SCHEMA, parse_intent, resolve  # noqa: F401
from pilot import verify_snapshot

SNAPSHOT = ROOT / "docs/audits/2026-09-07-coverage/pilot-snapshot.json"
MODEL = "gemma4:e4b"
DIGEST = "c6eb396dbd5992bbe3f5cdb947e8bbc0ee413d7c17e2beaae69f5d569cf982eb"
ALIASES = {
    "Samsung": r"삼성(?:전자)?|\bsamsung\b",
    "NAVER": r"네이버|\bnaver\b",
    "Microsoft": r"마이크로소프트|\bmicrosoft\b",
}
METRICS = {
    "revenue": r"매출(?:액)?|영업수익|\brevenue\b",
    "operating_income": r"영업이익|operating (?:income|profit)",
    "net_income": r"당기순이익|net (?:income|profit)",
    "research_and_development": r"연구개발비|R\s*&\s*D|research and development",
}


def validate_snapshot(snapshot):
    verify_snapshot(snapshot)
    ids = set()
    for f in snapshot["facts"]:
        if (
            f["id"] in ids
            or f["scale"] != 1
            or not re.fullmatch(r"-?\d+(\.\d+)?", f["value"])
        ):
            raise ValueError("Invalid or duplicate financial fact")
        ids.add(f["id"])
        source = f["source"]
        url = urlparse(source["url"])
        if (
            url.scheme != "https"
            or url.hostname not in ("dart.fss.or.kr", "www.sec.gov")
            or url.username
        ):
            raise ValueError("Unapproved filing destination")
        if not source["filing_identity"] or not source["document_sha256"]:
            raise ValueError("Missing provenance")
    return snapshot


def catalog(snapshot):
    return [
        {**f, "company": "Samsung" if f["company"] == "삼성전자" else f["company"]}
        for f in snapshot["facts"]
    ]


def financial_answer(intent, snapshot, question=""):
    answer = resolve(intent, catalog(snapshot))
    if answer["reason_code"] in (
        "missing_period",
        "incompatible_currency",
        "incompatible_comparison",
    ):
        supported = [
            f
            for f in catalog(snapshot)
            if f["company"] in intent["companies"]
            and f["period"] in intent["periods"]
            and f["metric"] == intent["metric"]
        ]
        answer["fact_ids"] = [f["id"] for f in supported]
        if supported:
            answer["partial"] = True
            answer["answer_ko"] = "확인된 수치만 표시합니다. " + answer["answer_ko"]
            answer["answer_en"] = (
                "Only supported figures are shown. " + answer["answer_en"]
            )
    by_id = {f["id"]: f for f in snapshot["facts"]}
    answer["figures"] = [copy.deepcopy(by_id[i]) for i in answer["fact_ids"]]
    answer["snapshot_id"] = snapshot["snapshot_id"]
    # These receipts describe the catalog actually inspected, never a full-filing search.
    answer["searched"] = list(
        {
            (
                f["source"]["filing_identity"],
                f["source"].get("section", "Inline XBRL facts"),
            ): {
                "filing_title": f["source"]["filing_title"],
                "section": f["source"].get("section", "Inline XBRL facts"),
                "company": f["company"],
                "period": f["period"],
            }
            for f in catalog(snapshot)
            if f["company"] in intent["companies"]
        }.values()
    )
    if re.search(r"\bwhy\b|왜|이유|원인", question, re.IGNORECASE) and not re.search(
        r"formula|calculat|계산|산식", question, re.IGNORECASE
    ):
        answer.update(
            operation="refuse",
            refused=True,
            reason_code="unsupported_causation",
            calculated=[],
            answer_ko="검증된 수치로 사업상 원인을 판단할 수 없습니다. 표시된 수치의 원문 공시에서 사업 설명을 확인해 주세요.",
            answer_en="Verified figures do not establish business causes. Consult the original filing for business discussion; only supported figures are shown.",
        )
    return answer


def guard_intent(question, intent, context):
    intent = copy.deepcopy(intent)
    explicit = {
        c
        for c, pattern in ALIASES.items()
        if re.search(pattern, question, re.IGNORECASE)
    }
    actual = set(intent["companies"])
    if len(explicit) == 1:
        intent["companies"] = sorted(explicit)
    elif explicit and actual != explicit:
        raise ValueError(
            "Company interpretation conflicts with the question; rephrase with one company"
        )
    if not explicit and not (context or {}).get("companies"):
        intent["companies"] = []
    elif not explicit and context and actual != set(context["companies"]):
        raise ValueError("An implicit follow-up cannot silently switch company")
    years = set(re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", question))
    if years and not years.issubset(set(intent["periods"])):
        raise ValueError("Fiscal year interpretation conflicts with the question")
    if not years and not (context or {}).get("periods"):
        intent["periods"] = []
    metrics = {
        m
        for m, pattern in METRICS.items()
        if re.search(pattern, question, re.IGNORECASE)
    }
    if not metrics and not (context or {}).get("metric"):
        intent["metric"] = None
    elif len(metrics) == 1 and intent["metric"] not in metrics:
        raise ValueError("Metric interpretation conflicts with the question")
    elif len(metrics) > 1:
        intent["metric"] = None
    return intent


def checksum(data):
    return hashlib.sha256(
        json.dumps(data, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
