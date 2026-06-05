from unittest.mock import patch

import src.rag as rag_module


def test_health_without_rag(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["rag_ready"] is False


def test_health_with_rag_ready(client):
    rag_module._rag_chain = object()
    try:
        response = client.get("/health")
        assert response.json()["rag_ready"] is True
    finally:
        rag_module._rag_chain = None


def test_legacy_chat_empty_message_returns_400(client):
    response = client.post("/api/chat", json={"msg": "   "})
    assert response.status_code == 400


@patch("src.app_factory.ensure_rag_chain", return_value=True)
@patch("src.app_factory.invoke_rag", return_value="Educational answer about fever.")
def test_legacy_chat_success(mock_invoke, _mock_ensure, client):
    response = client.post("/api/chat", json={"msg": "I have a fever"})

    assert response.status_code == 200
    assert response.json()["answer"] == "Educational answer about fever."
    mock_invoke.assert_called_once_with("I have a fever")


@patch("src.app_factory.ensure_rag_chain", return_value=True)
@patch("src.app_factory.invoke_rag", side_effect=RuntimeError("chain down"))
def test_legacy_chat_rag_failure_returns_503(mock_invoke, _mock_ensure, client):
    response = client.post("/api/chat", json={"msg": "headache"})

    assert response.status_code == 503
    assert "Unable to generate" in response.json()["detail"]


@patch("src.app_factory.ensure_rag_chain", return_value=True)
@patch("src.app_factory.invoke_rag", return_value="")
def test_legacy_chat_empty_model_response_returns_503(mock_invoke, _mock_ensure, client):
    response = client.post("/api/chat", json={"msg": "headache"})
    assert response.status_code == 503


def test_legacy_form_endpoint(client):
    with (
        patch("src.app_factory.ensure_rag_chain", return_value=True),
        patch("src.app_factory.invoke_rag", return_value="Form OK"),
    ):
        response = client.post("/get", data={"msg": "hello"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Form OK"
