APEX_REPORT_SNIPPET = """
Hemoglobin (Hgb) 13.8 g/dL 12.0 - 16.0 g/dL Normal
Glucose, Fasting 108 mg/dL 65 - 99 mg/dL High (H)
Creatinine 0.8 mg/dL 0.6 - 1.1 mg/dL Normal
Total Cholesterol 215 mg/dL < 200 mg/dL High (H)
HDL Cholesterol 55 mg/dL > 50 mg/dL Normal
LDL Cholesterol 138 mg/dL < 100 mg/dL High (H)
TSH (Thyroid) 2.1 mIU/L 0.4 - 4.5 mIU/L Normal
Vitamin D, 25-Hydroxy 22 ng/mL 30 - 100 ng/mL Low (L)
"""


def test_apex_mock_report_values():
    from src.services.lab_parser import parse_lab_values
    from src.services.lab_reference import load_lab_tests

    load_lab_tests.cache_clear()
    parsed = parse_lab_values(APEX_REPORT_SNIPPET)
    by_id = {item.test.id: item for item in parsed}

    assert by_id["hemoglobin"].value == 13.8
    assert by_id["glucose"].value == 108.0
    assert by_id["tsh"].value == 2.1
    assert by_id["ldl"].value == 138.0
    assert by_id["vitamin_d"].value == 22.0
    assert "tsh" in by_id
    assert by_id["tsh"].value != 22.0


def test_apex_report_interpretation():
    from src.services.lab_results_service import generate_lab_results_reply
    from src.services.lab_reference import load_lab_tests

    load_lab_tests.cache_clear()
    reply = generate_lab_results_reply(APEX_REPORT_SNIPPET)
    assert "2.1" in reply.content or "2.1" in str(reply.metadata)
    assert "13.8" in reply.content
    assert "22" in reply.content
    assert "138" in reply.content
    ids = {item.test_id for item in (reply.metadata.lab_results if reply.metadata else [])}
    assert "vitamin_d" in ids
    tsh = next(item for item in reply.metadata.lab_results if item.test_id == "tsh")
    assert tsh.value == 2.1
    assert tsh.status == "normal"
