import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv(override=True)

_ALL_MODES = frozenset({"symptoms", "appointment", "mental_health", "lab_results"})


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    pinecone_api_key: str
    groq_api_key: str
    pinecone_index_name: str = "medical-chatbot"
    groq_model: str = "llama-3.1-8b-instant"
    groq_temperature: float = 0.7
    groq_max_tokens: int = 512
    retrieval_k: int = 3
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    mental_health_temperature: float = 0.4
    lab_results_temperature: float = 0.3
    pinecone_mental_health_index_name: str | None = None
    pinecone_lab_results_index_name: str | None = None
    lazy_rag_init: bool = True
    rate_limit_per_minute: int = 30
    enable_mock_status: bool = True
    environment: str = "development"
    enabled_modes: frozenset[str] = field(default_factory=lambda: _ALL_MODES)

    def is_mode_enabled(self, mode: str) -> bool:
        return mode in self.enabled_modes

    @classmethod
    def from_env(cls) -> "Settings":
        pinecone_key = os.getenv("PINECONE_API_KEY", "").strip()
        groq_key = os.getenv("GROQ_API_KEY", "").strip()
        missing = [
            name
            for name, value in (
                ("PINECONE_API_KEY", pinecone_key),
                ("GROQ_API_KEY", groq_key),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required environment variables: {', '.join(missing)}"
            )
        os.environ["PINECONE_API_KEY"] = pinecone_key
        os.environ["GROQ_API_KEY"] = groq_key
        mh_index = os.getenv("PINECONE_MENTAL_HEALTH_INDEX_NAME", "").strip() or None
        lab_index = os.getenv("PINECONE_LAB_RESULTS_INDEX_NAME", "").strip() or None
        mh_temp = float(os.getenv("MENTAL_HEALTH_TEMPERATURE", "0.4"))
        lab_temp = float(os.getenv("LAB_RESULTS_TEMPERATURE", "0.3"))
        environment = os.getenv("ENVIRONMENT", "development").strip().lower()
        enable_mock_status = _env_bool(
            "ENABLE_MOCK_STATUS",
            default=environment != "production",
        )
        lazy_rag_init = _env_bool("LAZY_RAG_INIT", default=True)
        if _env_bool("EAGER_RAG_ON_STARTUP", default=False):
            lazy_rag_init = False
        rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
        modes_raw = os.getenv(
            "ENABLED_MODES",
            "symptoms,appointment,mental_health,lab_results",
        )
        enabled_modes = frozenset(
            mode.strip()
            for mode in modes_raw.split(",")
            if mode.strip() in _ALL_MODES
        ) or _ALL_MODES
        return cls(
            pinecone_api_key=pinecone_key,
            groq_api_key=groq_key,
            pinecone_mental_health_index_name=mh_index,
            pinecone_lab_results_index_name=lab_index,
            mental_health_temperature=mh_temp,
            lab_results_temperature=lab_temp,
            lazy_rag_init=lazy_rag_init,
            rate_limit_per_minute=rate_limit,
            enable_mock_status=enable_mock_status,
            environment=environment,
            enabled_modes=enabled_modes,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
