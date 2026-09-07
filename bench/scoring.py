"""Exact fact/source checks and a deliberately conservative numeric audit."""

import ast
import copy
import json
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

TOP_KEYS = {"answer_ko", "answer_en", "figures", "calculated", "refused", "refusal_reason"}
FIGURE_KEYS = {"label", "period", "value", "unit", "source"}
CALC_KEYS = {"label", "formula", "value", "inputs"}
NUMBER = re.compile(r"(?<![\w.])[-+−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?")


def decimal(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ValueError("not a decimal")
    result = Decimal(str(value).replace(",", "").replace("−", "-"))
    if not result.is_finite():
        raise ValueError("nonfinite decimal")
    return result


def number_tokens(value):
    if isinstance(value, dict):
        for child in value.values():
            yield from number_tokens(child)
    elif isinstance(value, list):
        for child in value:
            yield from number_tokens(child)
    elif isinstance(value, str):
        yield from NUMBER.findall(value)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        yield str(value)


def figure_from_row(row):
    return {key: copy.deepcopy(row[key]) for key in sorted(FIGURE_KEYS)}


def expected_figures(fixture, expected):
    figures = []
    for item in expected["figures"]:
        matches = [row for row in fixture["rows"]
                   if row["label"] == item["label"] and row["period"] == item["period"]]
        if len(matches) != 1 or decimal(matches[0]["value"]) != decimal(item["value"]):
            raise ValueError("Expected answer disagrees with fixture")
        figures.append(figure_from_row(matches[0]))
    return figures


def same_figure(actual, expected):
    if not isinstance(actual, dict) or set(actual) != FIGURE_KEYS:
        return False
    try:
        return (all(actual[key] == expected[key] for key in FIGURE_KEYS - {"value"})
                and isinstance(actual["value"], str)
                and decimal(actual["value"]) == decimal(expected["value"]))
    except (ValueError, InvalidOperation):
        return False


def same_figures(actual, expected):
    if not isinstance(actual, list) or len(actual) != len(expected):
        return False
    remaining = list(expected)
    for figure in actual:
        index = next((i for i, item in enumerate(remaining) if same_figure(figure, item)), None)
        if index is None:
            return False
        remaining.pop(index)
    return True


def formula_shape(expression):
    if not isinstance(expression, str) or len(expression) > 200:
        raise ValueError("Invalid formula")
    # AST comparison admits whitespace/parentheses, never executes model output.
    return ast.dump(ast.parse(expression.strip(), mode="eval"), include_attributes=False)


def valid_calculation(actual, expected, figures):
    if not isinstance(actual, dict) or set(actual) != CALC_KEYS:
        return False
    try:
        ordered = [next(f for f in figures if f["period"] == period)
                   for period in expected["input_periods"]]
        current, prior = [decimal(f["value"]) for f in ordered]
        computed = ((current - prior) / prior * 100).quantize(Decimal(".01"), rounding=ROUND_HALF_UP)
        return (actual["label"] == expected["label"]
                and isinstance(actual["value"], str)
                and decimal(actual["value"]) == decimal(expected["value"]) == computed
                and formula_shape(actual["formula"]) == formula_shape(expected["formula"])
                and isinstance(actual["inputs"], list) and len(actual["inputs"]) == len(ordered)
                and all(same_figure(a, b) for a, b in zip(actual["inputs"], ordered)))
    except (ValueError, SyntaxError, InvalidOperation, ZeroDivisionError, StopIteration, KeyError):
        return False


def reject_constant(value):
    raise ValueError(f"Non-JSON constant: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def score(content, fixture, expected, question):
    target = expected_figures(fixture, expected)
    result = {"json_parse_success": False, "schema_valid": False,
              "figure_exact_match": False, "calculation_correct": False,
              "refusal_correct": False, "accuracy": False,
              "invented_numbers": [], "novel_numbers": [], "refusal_violation": False}
    try:
        output = json.loads(content, parse_constant=reject_constant, object_pairs_hook=unique_object)
        result["json_parse_success"] = True
    except (ValueError, TypeError, RecursionError):
        output = content

    # The model sees normalized rows, not original-unit amounts or fixture provenance notes.
    table = {"company": fixture["company"], "rows": [figure_from_row(r) for r in fixture["rows"]],
             "metric_aliases": fixture["metric_aliases"]}
    supported = {decimal(token) for token in number_tokens(table)}
    supported.update(decimal(token) for token in number_tokens(question))
    allowed = set(supported)
    if isinstance(output, dict):
        figures, calculations = output.get("figures"), output.get("calculated")
        result["schema_valid"] = (
            set(output) == TOP_KEYS
            and all(isinstance(output.get(k), str) and output[k].strip() for k in ("answer_ko", "answer_en"))
            and type(output.get("refused")) is bool
            and (output.get("refusal_reason") is None or isinstance(output.get("refusal_reason"), str))
            and isinstance(figures, list) and isinstance(calculations, list)
            and all(isinstance(f, dict) and set(f) == FIGURE_KEYS for f in figures)
            and all(isinstance(c, dict) and set(c) == CALC_KEYS for c in calculations))
        result["figure_exact_match"] = same_figures(figures, target)
        wanted_calcs = expected["calculated"]
        result["calculation_correct"] = (
            isinstance(calculations, list) and len(calculations) == len(wanted_calcs)
            and all(valid_calculation(a, b, target) for a, b in zip(calculations, wanted_calcs)))
        if result["calculation_correct"]:
            for calc in wanted_calcs:
                allowed.add(decimal(calc["value"]))
        reason = output.get("refusal_reason")
        result["refusal_correct"] = (output.get("refused") is expected["refused"]
            and ((isinstance(reason, str) and bool(reason.strip()) and figures == [] and calculations == [])
                 if expected["refused"] else reason is None))
        result["refusal_violation"] = bool(expected["refused"] and (figures or calculations))

    # Formula constants are permitted only inside a verified formula, never in prose.
    audited = output
    if isinstance(output, dict) and result["calculation_correct"]:
        audited = dict(output)
        audited["calculated"] = [{k: v for k, v in c.items() if k != "formula"}
                                 for c in output.get("calculated", [])]
    for token in number_tokens(audited):
        value = decimal(token)
        if value not in supported:
            result["novel_numbers"].append(token)
        if value not in allowed:
            result["invented_numbers"].append(token)

    if expected["refused"] and isinstance(output, dict):
        # Even an amount borrowed from another supplied row is an invalid missing-metric answer.
        years = {decimal(row["period"]) for row in fixture["rows"]}
        narrative = [output.get(k, "") for k in ("answer_ko", "answer_en", "refusal_reason")]
        amounts = [token for token in number_tokens(narrative) if decimal(token) not in years]
        result["refusal_violation"] |= bool(amounts)
        result["invented_numbers"].extend(token for token in amounts if token not in result["invented_numbers"])
    result["accuracy"] = bool(all(result[k] for k in (
        "schema_valid", "figure_exact_match", "calculation_correct", "refusal_correct"))
        and not result["invented_numbers"] and not result["refusal_violation"])
    return result
