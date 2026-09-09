"""Pinned model configuration, question/context guards and compatibility exports."""

import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from slice.financial import SCHEMA, catalog, financial_answer, parse_intent, validate_snapshot

OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 256}

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








def _is_context_followup(question):
    """Carry company context only for a bounded company-free follow-up vocabulary."""
    remaining = question.lower()
    for pattern in METRICS.values():
        remaining = re.sub(pattern, " ", remaining, flags=re.IGNORECASE)
    remaining = re.sub(r"(?<!\d)(?:19|20)\d{2}(?!\d)", " ", remaining)
    remaining = re.sub(
        r"\b(?:what|how|about|and|the|its|it|that|same|company|was|is|were|in|for|of|"
        r"compare|versus|vs|change|growth|percent|percentage|please|show|me|then|fy|keep|metric|but)\b",
        " ", remaining,
    )
    remaining = re.sub(
        r"알려줘|보여줘|얼마인가요|얼마야|어때|같은\s*회사|그\s*회사|그럼|비교|대비|증감률|증가율|"
        r"수치|변화율|변화|은|는|이|가|의|을|를|과|와|년|도|엔|에", " ", remaining,
    )
    return not re.search(r"[\w]", remaining)


def guard_intent(question, intent, context):
    intent = copy.deepcopy(intent)
    explicit = {
        c
        for c, pattern in ALIASES.items()
        if re.search(pattern, question, re.IGNORECASE)
    }
    company_question = re.sub(
        r"연결\s*(?:이\s*아닌|이\s*아니라|말고|대신)\s*별도|"
        r"\bnot\s+consolidated\s*[,;]?\s*(?:but\s+)?separate\b|"
        r"\bseparate\s+rather\s+than\s+consolidated\b",
        " ", question, flags=re.IGNORECASE,
    )
    correction_requested = bool(re.search(
        r"\b(?:not|instead|except|excluding|without|unlike|ignore)\b|"
        r"\b(?:rather|other)\s+than\b|아니|아닌|말고|제외|대신|빼고", company_question, re.IGNORECASE
    ))
    corrected_company = None
    # Only a direct correction between two known names can narrow this set.
    if len(explicit) == 2:
        for excluded in explicit:
            selected = next(company for company in explicit if company != excluded)
            correction = (
                rf"^(?:{ALIASES[excluded]})(?:가|이)?\s*아니라\s*(?:{ALIASES[selected]})"
                rf"|^not\s+(?:{ALIASES[excluded]})\s*[,;]?\s*(?:but\s+)?(?:{ALIASES[selected]})"
            )
            match = re.search(correction, question.strip(), re.IGNORECASE)
            if match:
                if _is_context_followup(question.strip()[match.end():]):
                    corrected_company = selected
                break
    actual = set(intent["companies"])
    if correction_requested:
        intent["companies"] = [corrected_company] if corrected_company else []
    elif len(explicit) == 1:
        intent["companies"] = sorted(explicit)
    elif explicit and actual != explicit:
        intent["companies"] = []
    if not correction_requested and not explicit and not (context or {}).get("companies"):
        intent["companies"] = []
    elif not correction_requested and not explicit and context and not _is_context_followup(question):
        intent["companies"] = []
    elif not correction_requested and not explicit and context and actual != set(context["companies"]):
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
