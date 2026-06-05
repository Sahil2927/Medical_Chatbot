import pytest

from src.db.session import get_session_factory, init_db, reset_engine_cache
from src.persistence.conversation_store import PostgresConversationStore
from src.persistence import reset_conversation_store
from src.services.chat_service import DEFAULT_REPLY


@pytest.fixture
def store(monkeypatch) -> PostgresConversationStore:
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_engine_cache()
    reset_conversation_store()
    init_db()
    return PostgresConversationStore(get_session_factory())


def test_create_conversation_without_content(store: PostgresConversationStore):
    conversation, exchange = store.create_conversation(title="Test thread")

    assert exchange is None
    assert conversation["title"] == "Test thread"
    assert store.list_messages(conversation["id"]) == []


def test_add_message_exchange_persists_user_and_assistant(store: PostgresConversationStore):
    conversation, _ = store.create_conversation(mode="symptoms")
    exchange = store.add_message_exchange(
        conversation["id"],
        content="I have a headache",
        assistant_content="Assistant reply text",
        mode="symptoms",
    )

    messages = store.list_messages(conversation["id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"
    assert exchange.assistant_message.content == "Assistant reply text"


def test_list_conversations_sorted_by_updated_at(store: PostgresConversationStore):
    first, _ = store.create_conversation(title="First")
    second, _ = store.create_conversation(title="Second")
    store.add_message_exchange(
        first["id"],
        content="update first",
        assistant_content="reply",
    )

    listed = store.list_conversations()
    assert listed[0]["id"] == first["id"]
    assert listed[1]["id"] == second["id"]


def test_add_message_exchange_sets_mode_on_conversation(store: PostgresConversationStore):
    conversation, _ = store.create_conversation()
    store.add_message_exchange(
        conversation["id"],
        content="Book cardiology",
        assistant_content="booking info",
        mode="appointment",
    )

    updated = store.get_conversation(conversation["id"])
    assert updated is not None
    assert updated["mode"] == "appointment"


def test_add_message_exchange_unknown_conversation_raises(store: PostgresConversationStore):
    with pytest.raises(KeyError):
        store.add_message_exchange(
            "missing-id",
            content="hello",
            assistant_content="reply",
        )


def test_title_from_first_message_truncates_long_text(store: PostgresConversationStore):
    long_text = "a" * 50
    conversation, _ = store.create_conversation()
    store.add_message_exchange(
        conversation["id"],
        content=long_text,
        assistant_content=DEFAULT_REPLY,
    )

    updated = store.get_conversation(conversation["id"])
    assert updated is not None
    assert updated["title"].endswith("…")


def test_messages_survive_new_store_instance(store: PostgresConversationStore):
    conversation, _ = store.create_conversation(title="Persist me")
    store.add_message_exchange(
        conversation["id"],
        content="hello",
        assistant_content="hi back",
    )

    other = PostgresConversationStore(get_session_factory())
    messages = other.list_messages(conversation["id"])
    assert len(messages) == 2
