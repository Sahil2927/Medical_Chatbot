import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from src.app_factory import create_app
from src.db.models import AppointmentModel, ConversationModel, MessageModel, ProviderModel
from src.db.seed import seed_providers
from src.db.session import get_session_factory, init_db, reset_engine_cache
from src.persistence import reset_conversation_store
import src.lab_results_rag as lab_rag_module
import src.mental_health_rag as mh_rag_module
import src.rag as rag_module


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "0")
    monkeypatch.setenv("ENABLE_MOCK_STATUS", "true")
    monkeypatch.setenv("LAZY_RAG_INIT", "true")
    monkeypatch.delenv("USE_MEMORY_STORE", raising=False)
    rag_module._rag_chain = None
    mh_rag_module._mh_rag_chain = None
    lab_rag_module._lab_rag_chain = None
    mh_rag_module._mh_rag_chain = None
    lab_rag_module._lab_rag_chain = None
    reset_engine_cache()
    reset_conversation_store()
    from src.config import get_settings

    get_settings.cache_clear()
    init_db()
    yield
    _clear_database()
    reset_conversation_store()
    reset_engine_cache()
    rag_module._rag_chain = None
    mh_rag_module._mh_rag_chain = None
    lab_rag_module._lab_rag_chain = None


def _clear_database() -> None:
    with get_session_factory()() as session:
        session.execute(delete(AppointmentModel))
        session.execute(delete(MessageModel))
        session.execute(delete(ConversationModel))
        session.execute(delete(ProviderModel))
        session.commit()
    seed_providers(get_session_factory())


@pytest.fixture
def client() -> TestClient:
    application = create_app(load_rag_on_startup=False)
    with TestClient(application) as test_client:
        yield test_client
