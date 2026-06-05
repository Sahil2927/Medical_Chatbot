from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

LabStatus = Literal["low", "normal", "high", "unknown"]

_REFERENCE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "lab_reference.json"


@dataclass(frozen=True)
class LabTestDefinition:
    id: str
    display_name: str
    aliases: tuple[str, ...]
    default_unit: str
    accepted_units: tuple[str, ...]
    reference_min: float
    reference_max: float
    reference_unit: str
    reference_label: str
    notes: dict[str, str]
    plausible_min: float
    plausible_max: float


@dataclass(frozen=True)
class InterpretedLabResult:
    test_id: str
    display_name: str
    value: float
    unit: str
    status: LabStatus
    reference_range: str
    note: str


@lru_cache
def load_lab_tests() -> tuple[LabTestDefinition, ...]:
    with _REFERENCE_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    tests: list[LabTestDefinition] = []
    for row in data["tests"]:
        ref = row["reference"]
        plausible = row.get("plausible", {})
        plausible_min = float(plausible.get("min", ref["min"]))
        plausible_max = float(plausible.get("max", ref["max"]))
        tests.append(
            LabTestDefinition(
                id=row["id"],
                display_name=row["display_name"],
                aliases=tuple(a.lower() for a in row["aliases"]),
                default_unit=row["default_unit"],
                accepted_units=tuple(
                    u.lower() for u in row.get("accepted_units", [row["default_unit"]])
                ),
                reference_min=float(ref["min"]),
                reference_max=float(ref["max"]),
                reference_unit=ref["unit"],
                reference_label=ref["label"],
                notes=row["notes"],
                plausible_min=plausible_min,
                plausible_max=plausible_max,
            )
        )
    return tuple(tests)


def _alias_index() -> dict[str, LabTestDefinition]:
    index: dict[str, LabTestDefinition] = {}
    for test in load_lab_tests():
        for alias in test.aliases:
            index[alias] = test
        index[test.id] = test
    return index


def resolve_test(name_fragment: str) -> LabTestDefinition | None:
    lowered = name_fragment.lower().strip()
    index = _alias_index()
    if lowered in index:
        return index[lowered]
    matches = [alias for alias in index if alias in lowered or lowered in alias]
    if not matches:
        return None
    best_alias = max(matches, key=len)
    return index[best_alias]


def _normalize_unit(unit: str) -> str:
    return unit.strip().lower().replace("μ", "u")


def _unit_matches(test: LabTestDefinition, unit: str) -> bool:
    if not unit:
        return True
    normalized = _normalize_unit(unit)
    default = _normalize_unit(test.default_unit)
    return normalized == default or normalized in test.accepted_units


def evaluate_status(test: LabTestDefinition, value: float, unit: str) -> LabStatus:
    if not _unit_matches(test, unit):
        return "unknown"
    if value < test.plausible_min or value > test.plausible_max:
        return "unknown"
    if value < test.reference_min:
        return "low"
    if value > test.reference_max:
        return "high"
    return "normal"


def interpret_result(
    test: LabTestDefinition,
    value: float,
    unit: str,
) -> InterpretedLabResult:
    status = evaluate_status(test, value, unit)
    note = test.notes.get(status, test.notes.get("unknown", ""))
    if status == "unknown" and test.plausible_min <= value <= test.plausible_max:
        note = (
            f"{note} Value is outside the usual reference interval for {test.display_name}."
        ).strip()
    elif status == "unknown":
        note = (
            f"{note} This value looks unusual for {test.display_name} with unit {unit or test.default_unit} "
            "— confirm the test name and unit on your report."
        ).strip()
    return InterpretedLabResult(
        test_id=test.id,
        display_name=test.display_name,
        value=value,
        unit=unit or test.default_unit,
        status=status,
        reference_range=test.reference_label,
        note=note,
    )
