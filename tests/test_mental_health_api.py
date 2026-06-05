from unittest.mock import patch


def test_mental_health_crisis_returns_metadata(client):
    created = client.post("/api/conversations", json={"mode": "mental_health"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "I want to kill myself"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body.get("metadata") is not None
    assert body["metadata"]["crisis_detected"] is True
    assert len(body["metadata"]["helplines"]) >= 1
    assert "988" in body["assistant_message"]["content"]


@patch(
    "src.services.mental_health_service.invoke_mental_health_chat",
    return_value="It can help to talk with someone you trust about how you feel.",
)
def test_mental_health_non_crisis_uses_groq(mock_chat, client):
    created = client.post("/api/conversations", json={"mode": "mental_health"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "I have been feeling anxious lately"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body.get("metadata") is None
    assert "trust" in body["assistant_message"]["content"].lower()
    mock_chat.assert_called_once()
