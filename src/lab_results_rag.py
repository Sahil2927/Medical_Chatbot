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
from src.prompts.lab_results import LAB_RESULTS_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_lab_rag_chain: Any | None = None

LAB_RESULTS_RAG_PROMPT = (
    LAB_RESULTS_SYSTEM_PROMPT
    + "\n\nUse the following context when it is relevant. If context is empty or not helpful, "
    "provide general educational guidance only.\n\n{context}"
)


def _lab_results_index_name() -> str | None:
    name = os.getenv("PINECONE_LAB_RESULTS_INDEX_NAME", "").strip()
    return name or None


def build_lab_results_rag_chain(index_name: str):
    settings = get_settings()
    logger.info("Loading lab results RAG for Pinecone index '%s'", index_name)
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
        temperature=settings.lab_results_temperature,
        max_tokens=settings.groq_max_tokens,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", LAB_RESULTS_RAG_PROMPT),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def init_lab_results_chain() -> None:
    ensure_lab_results_chain()


def ensure_lab_results_chain() -> bool:
    global _lab_rag_chain
    index_name = _lab_results_index_name()
    if not index_name:
        return False
    if _lab_rag_chain is not None:
        return True
    try:
        _lab_rag_chain = build_lab_results_rag_chain(index_name)
        logger.info("Lab results RAG chain ready (index=%s)", index_name)
        return True
    except Exception:
        logger.exception("Failed to initialize lab results RAG chain")
        return False


def is_lab_results_rag_ready() -> bool:
    return _lab_rag_chain is not None


def invoke_lab_results_rag(user_message: str) -> str:
    if not ensure_lab_results_chain():
        raise RuntimeError("Lab results RAG chain is not initialized")
    result = _lab_rag_chain.invoke({"input": user_message})
    return str(result.get("answer", "")).strip()
