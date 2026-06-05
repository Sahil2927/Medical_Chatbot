import pytest

from src.config import Settings, get_settings


def test_settings_from_env_reads_required_keys(monkeypatch):
    monkeypatch.setenv("PINECONE_API_KEY", "pk-test")
    monkeypatch.setenv("GROQ_API_KEY", "gk-test")
    get_settings.cache_clear()

    settings = Settings.from_env()

    assert settings.pinecone_api_key == "pk-test"
    assert settings.groq_api_key == "gk-test"
    assert settings.pinecone_index_name == "medical-chatbot"
    assert settings.groq_model == "llama-3.1-8b-instant"


def test_settings_from_env_raises_when_keys_missing(monkeypatch):
    monkeypatch.delenv("PINECONE_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    get_settings.cache_clear()

    with pytest.raises(RuntimeError, match="PINECONE_API_KEY"):
        Settings.from_env()
