import logging
import os
from typing import Any

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore

from src.config import get_settings
from src.helper import download_hugging_face_embeddings
from src.prompts.mental_health import (
    MENTAL_HEALTH_RAG_CONTEXT_RULES,
    MENTAL_HEALTH_SYSTEM_PROMPT,
)

logger = logging.getLogger(__name__)

_mh_rag_chain: Any | None = None

MENTAL_HEALTH_RAG_PROMPT = (
    MENTAL_HEALTH_SYSTEM_PROMPT
    + "\n\n"
    + MENTAL_HEALTH_RAG_CONTEXT_RULES
    + "\n\nReference material (do not quote verbatim):\n{context}"
)


def _mental_health_index_name() -> str | None:
    name = os.getenv("PINECONE_MENTAL_HEALTH_INDEX_NAME", "").strip()
    return name or None


def build_mental_health_rag_chain(index_name: str):
    settings = get_settings()
    logger.info(
        "Loading mental health RAG for Pinecone index '%s'",
        index_name,
    )
    embeddings = download_hugging_face_embeddings()
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=index_name,
        embedding=embeddings,
    )
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retrieval_k},
    )
    chat_model = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.mental_health_temperature,
        max_tokens=settings.groq_max_tokens,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", MENTAL_HEALTH_RAG_PROMPT),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def init_mental_health_chain() -> None:
    ensure_mental_health_chain()


def ensure_mental_health_chain() -> bool:
    global _mh_rag_chain
    index_name = _mental_health_index_name()
    if not index_name:
        return False
    if _mh_rag_chain is not None:
        return True
    try:
        _mh_rag_chain = build_mental_health_rag_chain(index_name)
        logger.info("Mental health RAG chain ready (index=%s)", index_name)
        return True
    except Exception:
        logger.exception("Failed to initialize mental health RAG chain")
        return False


def is_mental_health_rag_ready() -> bool:
    return _mh_rag_chain is not None


def invoke_mental_health_rag(user_message: str) -> str:
    if not ensure_mental_health_chain():
        raise RuntimeError("Mental health RAG chain is not initialized")
    result = _mh_rag_chain.invoke({"input": user_message})
    return str(result.get("answer", "")).strip()
