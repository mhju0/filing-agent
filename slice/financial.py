"""Deterministic Financial figure policy shared by investigations and experiments."""

import copy
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import urlparse


def reject_constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


SCHEMA = {'type': 'object', 'properties': {
    'companies': {'type': 'array', 'items': {'type': 'string', 'enum': ['Samsung', 'NAVER', 'Microsoft']}},
    'metric': {'type': ['string', 'null'], 'enum': ['revenue', 'operating_income', 'net_income', 'research_and_development', None]},
    'periods': {'type': 'array', 'items': {'type': 'string', 'pattern': '^[0-9]{4}$'}},
    'basis': {'type': 'string', 'enum': ['consolidated', 'separate']},
    'action': {'type': 'string', 'enum': ['report', 'compare']}},
    'required': ['companies', 'metric', 'periods', 'basis', 'action'], 'additionalProperties': False}


COPY = {
    'outside_verified_metric_scope': ('현재 검증된 근거 범위에는 요청한 지표가 없습니다. 공시 전체에 없다는 뜻은 아닙니다.', 'The requested metric is outside the verified evidence scope; this does not mean it is absent from the entire filing.'),
    'missing_period': ('요청한 회사와 연도에 해당하는 검증된 수치가 없습니다.', 'No verified figure is available for the requested company and fiscal year.'),
    'unsupported_basis': ('현재 검증된 근거는 연결 기준입니다. 별도 기준 수치는 제공할 수 없습니다.', 'The verified evidence is consolidated; separate-statement figures are unavailable.'),
    'incompatible_currency': ('통화가 달라 증감률을 계산할 수 없습니다.', 'A percentage change cannot be calculated across different currencies.'),
    'incompatible_comparison': ('현재 근거로는 요청한 증감률을 계산할 수 없습니다.', 'The requested percentage change is not supported by comparable evidence.'),
    'ambiguous_context': ('회사, 지표 또는 회계연도를 지정해 주세요.', 'Please specify the company, metric, or fiscal year.'),
}


def parse_intent(content):
    intent = json.loads(content, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(intent, dict) or set(intent) != set(SCHEMA['required']):
        raise ValueError('Invalid intent keys')
    for key in ('companies', 'periods'):
        if not isinstance(intent[key], list) or not all(isinstance(x, str) for x in intent[key]) or len(set(intent[key])) != len(intent[key]):
            raise ValueError('Invalid intent list')
    if any(c not in ('Samsung', 'NAVER', 'Microsoft') for c in intent['companies']):
        raise ValueError('Unknown company')
    if any(not re.fullmatch(r'[0-9]{4}', p) for p in intent['periods']):
        raise ValueError('Invalid fiscal year')
    if intent['metric'] not in SCHEMA['properties']['metric']['enum'] or intent['basis'] not in ('consolidated', 'separate') or intent['action'] not in ('report', 'compare'):
        raise ValueError('Invalid intent enum')
    return intent


def verify_snapshot(snapshot):
    content = {k: v for k, v in snapshot.items() if k != 'snapshot_id'}
    digest = hashlib.sha256(json.dumps(content, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    if snapshot.get('snapshot_id') != 'sha256:' + digest:
        raise ValueError('Pilot snapshot changed without a new verified identity')


def calculated(facts):
    if len(facts) != 2:
        raise ValueError('A change requires exactly two figures')
    prior, current = sorted(facts, key=lambda fact: fact['period'])
    if any(prior[k] != current[k] for k in ('company', 'metric', 'currency', 'basis')):
        raise ValueError('Incompatible comparison')
    if any(prior[k][5:] != current[k][5:] for k in ('period_start', 'period_end')):
        raise ValueError('Incompatible fiscal-period definitions')
    if Decimal(prior['value']) <= 0:
        raise ValueError('Nonpositive prior baseline')
    delta = Decimal(current['value']) - Decimal(prior['value'])
    return {'inputs': [current['id'], prior['id']], 'absolute_change': str(delta),
            'percentage_change': str((delta / Decimal(prior['value']) * 100).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)),
            'currency': prior['currency']}


def resolve(intent, catalog):
    result = {'companies': intent['companies'], 'metric': intent['metric'], 'periods': intent['periods'],
              'operation': intent['action'], 'fact_ids': [], 'refused': False, 'reason_code': None,
              'figures': [], 'calculated': [], 'answer_ko': '', 'answer_en': ''}
    def blocked(reason):
        result.update(operation='clarify' if reason == 'ambiguous_context' else 'refuse',
                      refused=reason != 'ambiguous_context', reason_code=reason)
        result['answer_ko'], result['answer_en'] = COPY[reason]
        return result
    if not intent['companies'] or not intent['periods'] or intent['metric'] is None:
        return blocked('ambiguous_context')
    if intent['basis'] != 'consolidated':
        return blocked('unsupported_basis')
    if intent['metric'] not in {f['metric'] for f in catalog}:
        return blocked('outside_verified_metric_scope')
    selected = [f for f in catalog if f['company'] in intent['companies'] and f['period'] in intent['periods'] and f['metric'] == intent['metric'] and f['basis'] in ('consolidated', 'consolidated_entity_total')]
    if len(selected) != len(intent['companies']) * len(intent['periods']):
        return blocked('missing_period')
    if intent['action'] == 'compare':
        if len({f['currency'] for f in selected}) != 1:
            return blocked('incompatible_currency')
        try:
            change = calculated(selected)
        except ValueError:
            return blocked('incompatible_comparison')
        result['calculated'] = [change]
        # Sign and both languages come from the same checked arithmetic result.
        sign = Decimal(change['absolute_change'])
        ko, en = ('감소했습니다', 'decreased') if sign < 0 else (('증가했습니다', 'increased') if sign > 0 else ('동일합니다', 'was unchanged'))
        company = intent['companies'][0]
        company_ko = {'Samsung': '삼성전자', 'NAVER': '네이버', 'Microsoft': '마이크로소프트'}[company]
        metric_ko, metric_en = {'revenue': ('매출액', 'revenue'), 'operating_income': ('영업이익', 'operating income'), 'net_income': ('당기순이익', 'net income')}[intent['metric']]
        prior, current = sorted(intent['periods'])
        result['answer_ko'] = f'{company_ko}의 {current}년 {metric_ko}은 {prior}년보다 {ko}.' if sign else f'{company_ko}의 {current}년 {metric_ko}은 {prior}년과 {ko}.'
        result['answer_en'] = f"{company}'s {metric_en} {en} in FY{current} compared with FY{prior}."
    else:
        result['answer_ko'] = '요청한 회사, 지표, 회계연도의 검증된 수치입니다.'
        result['answer_en'] = 'These are the verified figures for the requested company, metric and fiscal year.'
    result['figures'] = selected
    result['fact_ids'] = [f['id'] for f in selected]
    return result


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
