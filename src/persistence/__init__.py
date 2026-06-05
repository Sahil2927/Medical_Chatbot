import os

from src.db.session import get_session_factory, reset_engine_cache
from src.persistence.conversation_store import PostgresConversationStore

_conversation_store = None


def get_conversation_store():
    global _conversation_store
    if _conversation_store is not None:
        return _conversation_store

    use_memory = os.getenv("USE_MEMORY_STORE", "").lower() in ("1", "true", "yes")
    if use_memory:
        from src.mock.store import mock_store

        _conversation_store = mock_store
    else:
        _conversation_store = PostgresConversationStore(get_session_factory())
    return _conversation_store


def configure_conversation_store(store) -> None:
    global _conversation_store
    _conversation_store = store


def reset_conversation_store() -> None:
    global _conversation_store
    _conversation_store = None
    reset_engine_cache()


__all__ = [
    "PostgresConversationStore",
    "configure_conversation_store",
    "get_conversation_store",
    "reset_conversation_store",
]
