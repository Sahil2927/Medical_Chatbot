def test_mock_status(client):
    response = client.get("/api/mock/status")

    assert response.status_code == 200
    body = response.json()
    assert body["mock"] is False
    assert "phase-b7" in body["version"]
    assert "symptoms" in body["supported_modes"]
    assert len(body["supported_modes"]) == 4


def test_create_and_list_conversations(client):
    create = client.post(
        "/api/conversations",
        json={"title": "Headache", "mode": "symptoms"},
    )
    assert create.status_code == 201
    created = create.json()
    assert created["title"] == "Headache"
    assert created["mode"] == "symptoms"

    listing = client.get("/api/conversations")
    assert listing.status_code == 200
    conversations = listing.json()["conversations"]
    assert len(conversations) == 1
    assert conversations[0]["id"] == created["id"]


def test_create_conversation_with_initial_content(client):
    response = client.post(
        "/api/conversations",
        json={
            "mode": "mental_health",
            "content": "I feel anxious",
        },
    )
    assert response.status_code == 201
    conversation_id = response.json()["id"]

    messages = client.get(f"/api/conversations/{conversation_id}/messages")
    assert messages.status_code == 200
    assert len(messages.json()["messages"]) == 2


def test_get_conversation_not_found(client):
    response = client.get("/api/conversations/does-not-exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_post_message_exchange_symptoms_uses_rag(client):
    from unittest.mock import patch

    created = client.post("/api/conversations", json={})
    conversation_id = created.json()["id"]

    import src.rag as rag_module

    rag_module._rag_chain = object()
    try:
        with patch(
            "src.services.chat_service.invoke_rag",
            return_value="Educational info about hypertension.",
        ):
            response = client.post(
                f"/api/conversations/{conversation_id}/messages",
                json={"content": "What is hypertension?", "mode": "symptoms"},
            )
        assert response.status_code == 201
        body = response.json()
        assert body["user_message"]["content"] == "What is hypertension?"
        assert "hypertension" in body["assistant_message"]["content"].lower()
        assert body["conversation"]["mode"] == "symptoms"
    finally:
        rag_module._rag_chain = None


def test_post_message_symptoms_without_rag_returns_503(client):
    created = client.post("/api/conversations", json={})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "headache", "mode": "symptoms"},
    )
    assert response.status_code == 503


def test_post_message_validation_error(client):
    created = client.post("/api/conversations", json={})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": ""},
    )
    assert response.status_code == 422


def test_post_message_unknown_conversation(client):
    response = client.post(
        "/api/conversations/unknown/messages",
        json={"content": "hello"},
    )
    assert response.status_code == 404


def test_list_messages_unknown_conversation(client):
    response = client.get("/api/conversations/unknown/messages")
    assert response.status_code == 404


def test_appointment_mode_reply_content(client):
    created = client.post(
        "/api/conversations",
        json={"mode": "appointment", "content": "Need a cardiologist"},
    )
    conversation_id = created.json()["id"]
    messages = client.get(f"/api/conversations/{conversation_id}/messages").json()[
        "messages"
    ]
    assert "Dr. Patel" in messages[-1]["content"] or "specialist" in messages[-1]["content"].lower()
