from unittest.mock import patch

import pytest

from src.db.session import get_session_factory, init_db, reset_engine_cache
from src.persistence import reset_conversation_store
from src.persistence.conversation_store import PostgresConversationStore
from src.services.chat_service import ChatService
from src.services.exceptions import ChatServiceError
import src.rag as rag_module


@pytest.fixture
def store(monkeypatch) -> PostgresConversationStore:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_engine_cache()
    reset_conversation_store()
    init_db()
    return PostgresConversationStore(get_session_factory())


@pytest.fixture
def service(store: PostgresConversationStore) -> ChatService:
    return ChatService(store)


def test_generate_reply_appointment(service: ChatService):
    reply = service.generate_reply("Need a cardiologist", "appointment")
    assert "Dr. Nguyen" in reply.content or "Cardiology" in reply.content


def test_generate_reply_mental_health_crisis(service: ChatService):
    reply = service.generate_reply("I feel suicidal", "mental_health")
    assert "988" in reply.content or "emergency" in reply.content.lower()
    assert reply.metadata is not None
    assert reply.metadata.crisis_detected is True


def test_generate_reply_lab_results_with_values(service: ChatService):
    reply = service.generate_reply("glucose 126 mg/dL", "lab_results")
    assert "glucose" in reply.content.lower()
    assert "healthcare provider" in reply.content.lower()
    assert reply.metadata is not None
    assert reply.metadata.lab_results[0].status == "high"


def test_symptoms_requires_rag_ready(service: ChatService):
    rag_module._rag_chain = None
    with pytest.raises(ChatServiceError, match="unavailable"):
        service.generate_reply("headache", "symptoms")


@patch("src.services.chat_service.invoke_rag", return_value="RAG-based symptom guidance.")
def test_symptoms_uses_rag(mock_invoke, service: ChatService):
    rag_module._rag_chain = object()
    try:
        reply = service.generate_reply("headache and fever", "symptoms")
        assert reply.content == "RAG-based symptom guidance."
        mock_invoke.assert_called_once_with("headache and fever")
    finally:
        rag_module._rag_chain = None


@patch("src.services.chat_service.invoke_rag", return_value="Answer")
def test_send_message_persists_exchange(mock_invoke, service: ChatService):
    rag_module._rag_chain = object()
    try:
        conversation, _ = service._store.create_conversation(mode="symptoms")
        exchange = service.send_message(
            conversation["id"],
            "I have a cough",
            "symptoms",
        )
        assert exchange.user_message.content == "I have a cough"
        assert exchange.assistant_message.content == "Answer"
        loaded = service._store.list_messages(conversation["id"])
        assert len(loaded) == 2
    finally:
        rag_module._rag_chain = None


def test_send_message_unknown_conversation(service: ChatService):
    with pytest.raises(ChatServiceError) as exc_info:
        service.send_message("missing", "hello", None)
    assert exc_info.value.status_code == 404
