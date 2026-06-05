from __future__ import annotations

import re
from dataclasses import dataclass

from src.services.lab_reference import LabTestDefinition, load_lab_tests, resolve_test

# Panel line: test name, optional (Hgb) / , Fasting, then result (PDF table rows)
_PATTERN_PANEL = re.compile(
    r"\b(?P<name>"
    r"total\s+cholesterol|ldl\s+cholesterol|ldl-c|ldl|"
    r"hdl\s+cholesterol|hdl-c|hdl|"
    r"hemoglobin|haemoglobin|hgb|hb|"
    r"glucose(?:,\s*fasting)?|fasting\s+glucose|blood\s+glucose|"
    r"vitamin\s+d(?:,\s*25[-\s]?hydroxy)?|25[-\s]?hydroxy|"
    r"tsh(?:\s*\(thyroid\))?|thyroid\s+stimulating\s+hormone|"
    r"serum\s+creatinine|creatinine|creat"
    r")"
    r"(?:\s*\([^)]{0,30}\))?"
    r"(?:,\s*[^0-9\n]{0,30})?"
    r"\s*[:=]?\s*"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>(?:mg/dL|mg/dl|g/dL|g/dl|mIU/L|miu/l|µIU/mL|ng/mL|ng/ml))?",
    re.IGNORECASE,
)

_REFERENCE_RANGE_SNIPPET = re.compile(r"\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?")

_PATTERN_NAME_VALUE = re.compile(
    r"(?P<name>[a-zA-Z][a-zA-Z0-9\s\-]{0,40}?)\s+"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[a-zA-Z][a-zA-Z0-9/%µμ\.]{0,12})?",
    re.IGNORECASE,
)

_PATTERN_VALUE_NAME = re.compile(
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?P<unit>[a-zA-Z][a-zA-Z0-9/%µμ\.]{0,12})?\s+"
    r"(?P<name>[a-zA-Z][a-zA-Z0-9\s\-]{1,40})",
    re.IGNORECASE,
)

_MAX_RESULTS = 8


@dataclass(frozen=True)
class ParsedLabValue:
    test: LabTestDefinition
    value: float
    unit: str
    raw_name: str


def _normalize_unit(unit: str) -> str:
    return unit.strip().lower().replace("μ", "u")


def _coerce_test_and_unit(
    test: LabTestDefinition,
    value: float,
    unit: str,
    raw_name: str,
) -> tuple[LabTestDefinition, float, str] | None:
    normalized = _normalize_unit(unit)

    # g/dL is essentially always hemoglobin in this panel
    if normalized == "g/dl":
        hemoglobin = resolve_test("hemoglobin")
        if hemoglobin:
            return hemoglobin, value, "g/dL"

    # 10–20 with g/dL unit missing often means hemoglobin, not LDL (12 g/dL misread as LDL 12 mg/dL)
    if test.id == "ldl" and 10 <= value <= 20 and normalized in ("", "mg/dl"):
        hemoglobin = resolve_test("hemoglobin")
        if hemoglobin:
            return hemoglobin, value, "g/dL"

    # LDL in mg/dL below 40 is rare — do not treat as normal LDL without a strong unit match
    if test.id == "ldl" and value < 40 and normalized != "mg/dl":
        return None

    if test.id == "ldl" and value < 40:
        hemoglobin = resolve_test("hemoglobin")
        if hemoglobin and 10 <= value <= 20:
            return hemoglobin, value, "g/dL"

    if normalized == "ng/ml" and test.id != "vitamin_d":
        return None

    if not unit:
        return test, value, test.default_unit

    return test, value, unit


def _reject_loose_match(raw_name: str, unit: str, from_panel: bool) -> bool:
    if from_panel:
        return False
    if "\n" in raw_name:
        return True
    if len(raw_name) > 45:
        return True
    if _REFERENCE_RANGE_SNIPPET.search(raw_name):
        return True
    letters = re.sub(r"[^a-zA-Z]", "", raw_name)
    if len(letters) < 2:
        return True
    normalized = _normalize_unit(unit)
    if normalized == "ng/ml" and "vitamin" not in raw_name.lower() and "hydroxy" not in raw_name.lower():
        return True
    return False


def _score_candidate(
    test: LabTestDefinition,
    value: float,
    unit: str,
    raw_name: str,
    *,
    from_panel: bool,
) -> int:
    score = 100 if from_panel else 0
    normalized = _normalize_unit(unit)
    default = _normalize_unit(test.default_unit)
    if normalized and (normalized == default or normalized in test.accepted_units):
        score += 40
    elif not unit:
        score += 5
    else:
        score -= 20
    if test.plausible_min <= value <= test.plausible_max:
        score += 25
    else:
        score -= 30
    score += min(len(raw_name), 30)
    return score


def _add_candidate(
    candidates: dict[str, tuple[ParsedLabValue, int]],
    *,
    raw_name: str,
    value: float,
    unit: str,
    from_panel: bool,
) -> None:
    if _reject_loose_match(raw_name, unit, from_panel):
        return

    test = resolve_test(raw_name)
    if not test:
        return

    coerced = _coerce_test_and_unit(test, value, unit, raw_name)
    if coerced is None:
        return

    test, value, unit = coerced
    parsed = ParsedLabValue(
        test=test,
        value=value,
        unit=unit,
        raw_name=raw_name,
    )
    score = _score_candidate(test, value, unit, raw_name, from_panel=from_panel)
    existing = candidates.get(test.id)
    if existing is None or score > existing[1]:
        candidates[test.id] = (parsed, score)


def parse_lab_values(text: str) -> list[ParsedLabValue]:
    candidates: dict[str, tuple[ParsedLabValue, int]] = {}

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        lines = [text]

    for line in lines:
        for match in _PATTERN_PANEL.finditer(line):
            _add_candidate(
                candidates,
                raw_name=match.group("name"),
                value=float(match.group("value")),
                unit=(match.group("unit") or "").strip(),
                from_panel=True,
            )

        for pattern in (_PATTERN_NAME_VALUE, _PATTERN_VALUE_NAME):
            for match in pattern.finditer(line):
                _add_candidate(
                    candidates,
                    raw_name=match.group("name").strip(),
                    value=float(match.group("value")),
                    unit=(match.groupdict().get("unit") or "").strip(),
                    from_panel=False,
                )

    ordered = sorted(candidates.values(), key=lambda item: item[1], reverse=True)
    return [item[0] for item in ordered[:_MAX_RESULTS]]
