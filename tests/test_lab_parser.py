from src.services.lab_parser import parse_lab_values
from src.services.lab_reference import evaluate_status, load_lab_tests, resolve_test


def test_resolve_test_glucose_alias():
    test = resolve_test("fasting glucose")
    assert test is not None
    assert test.id == "glucose"


def test_parse_glucose_value():
    parsed = parse_lab_values("My glucose 126 mg/dL from last week")
    assert len(parsed) == 1
    assert parsed[0].test.id == "glucose"
    assert parsed[0].value == 126.0
    assert "mg" in parsed[0].unit.lower()


def test_parse_multiple_tests():
    parsed = parse_lab_values("glucose 126 mg/dL and hemoglobin 10.5 g/dL")
    assert len(parsed) == 2
    ids = {item.test.id for item in parsed}
    assert ids == {"glucose", "hemoglobin"}


def test_evaluate_glucose_high():
    from src.services.lab_reference import load_lab_tests

    load_lab_tests.cache_clear()
    glucose = next(t for t in load_lab_tests() if t.id == "glucose")
    assert evaluate_status(glucose, 126.0, "mg/dL") == "high"


def test_parse_panel_report():
    from src.services.lab_reference import load_lab_tests

    load_lab_tests.cache_clear()
    text = """
    TSH 4.0 mIU/L
    Hemoglobin 12.0 g/dL
    LDL Cholesterol 120 mg/dL
    Glucose 108 mg/dL
    Creatinine 0.8 mg/dL
    Total Cholesterol 215 mg/dL
    HDL 55 mg/dL
    """
    parsed = parse_lab_values(text)
    ids = {item.test.id for item in parsed}
    assert "hemoglobin" in ids
    assert "ldl" in ids
    hb = next(item for item in parsed if item.test.id == "hemoglobin")
    assert hb.value == 12.0
    ldl = next(item for item in parsed if item.test.id == "ldl")
    assert ldl.value == 120.0


def test_ldl_12_reassigned_to_hemoglobin():
    from src.services.lab_reference import load_lab_tests

    load_lab_tests.cache_clear()
    parsed = parse_lab_values("LDL 12.0 g/dL")
    assert len(parsed) == 1
    assert parsed[0].test.id == "hemoglobin"
    assert parsed[0].value == 12.0
