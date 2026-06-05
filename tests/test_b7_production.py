from unittest.mock import patch

import pytest

from src.middleware.rate_limit import InMemoryRateLimiter


def test_mock_status_hidden_in_production(client, monkeypatch):
    monkeypatch.setenv("ENABLE_MOCK_STATUS", "false")
    from src.config import get_settings

    get_settings.cache_clear()

    application = __import__("src.app_factory", fromlist=["create_app"]).create_app(
        load_rag_on_startup=False,
    )
    with __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient(
        application,
    ) as test_client:
        response = test_client.get("/api/mock/status")
    assert response.status_code == 404


def test_request_id_header_on_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_rate_limiter_blocks_excess_requests():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is True
    assert limiter.is_allowed("client-a") is False


def test_rate_limit_returns_429(client, monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "1")
    from src.config import get_settings

    get_settings.cache_clear()

    application = __import__("src.app_factory", fromlist=["create_app"]).create_app(
        load_rag_on_startup=False,
    )
    TestClient = __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient

    AssistantReply = __import__(
        "src.services.reply_types", fromlist=["AssistantReply"]
    ).AssistantReply
    with patch(
        "src.services.mental_health_service.generate_mental_health_reply",
        return_value=AssistantReply(content="ok"),
    ):
        with TestClient(application) as test_client:
            created = test_client.post(
                "/api/conversations",
                json={"mode": "mental_health"},
            )
            conversation_id = created.json()["id"]
            first = test_client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "hello"},
            )
            second = test_client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "again"},
            )
    assert first.status_code == 201
    assert second.status_code == 429


def test_disabled_mode_returns_503(client, monkeypatch):
    monkeypatch.setenv("ENABLED_MODES", "appointment,mental_health,lab_results")
    from src.config import get_settings

    get_settings.cache_clear()

    application = __import__("src.app_factory", fromlist=["create_app"]).create_app(
        load_rag_on_startup=False,
    )
    TestClient = __import__("fastapi.testclient", fromlist=["TestClient"]).TestClient

    with TestClient(application) as test_client:
        created = test_client.post("/api/conversations", json={"mode": "symptoms"})
        response = test_client.post(
            "/api/conversations",
            json={"mode": "symptoms", "content": "headache"},
        )
    assert created.status_code == 503
    assert response.status_code == 503
    assert "disabled" in response.json()["detail"].lower()


@patch("src.rag.build_rag_chain")
def test_lazy_rag_loads_on_first_symptoms_message(mock_build, client, monkeypatch):
    import src.rag as rag_module

    monkeypatch.setenv("LAZY_RAG_INIT", "true")
    from src.config import get_settings

    get_settings.cache_clear()
    rag_module._rag_chain = None
    mock_build.return_value = object()

    with patch("src.services.chat_service.invoke_rag", return_value="Symptom guidance."):
        created = client.post("/api/conversations", json={"mode": "symptoms"})
        conversation_id = created.json()["id"]
        rag_module._rag_chain = None
        response = client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={"content": "headache"},
        )

    assert response.status_code == 201
    mock_build.assert_called_once()
