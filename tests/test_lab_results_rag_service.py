from unittest.mock import patch

from src.services.lab_results_service import generate_lab_results_reply


@patch(
    "src.services.lab_results_service.ensure_lab_results_chain",
    return_value=False,
)
def test_lab_results_no_values_without_rag(_mock_ready):
    reply = generate_lab_results_reply("Can you explain my blood work?")
    assert reply.metadata is None
    assert "hemoglobin" in reply.content.lower()


@patch(
    "src.services.lab_results_service.invoke_lab_results_rag",
    return_value="TSH helps regulate thyroid hormone production.",
)
@patch(
    "src.services.lab_results_service.ensure_lab_results_chain",
    return_value=True,
)
def test_lab_results_no_values_uses_rag(_mock_ready, _mock_invoke):
    reply = generate_lab_results_reply("What does TSH mean?")
    assert reply.metadata is None
    assert "TSH helps regulate" in reply.content
    assert "healthcare provider" in reply.content.lower()


@patch(
    "src.services.lab_results_service.invoke_lab_results_rag",
    return_value="Elevated fasting glucose may warrant follow-up with a clinician.",
)
@patch(
    "src.services.lab_results_service.ensure_lab_results_chain",
    return_value=True,
)
def test_lab_results_parsed_values_include_rag_narrative(_mock_ready, _mock_invoke):
    reply = generate_lab_results_reply("glucose 126 mg/dL")
    assert reply.metadata is not None
    assert len(reply.metadata.lab_results) == 1
    assert reply.metadata.lab_results[0].test_id == "glucose"
    assert "Additional context from the knowledge base" in reply.content
    assert "Elevated fasting glucose" in reply.content
    _mock_invoke.assert_called_once()
