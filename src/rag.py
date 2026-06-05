import logging
from typing import Any

from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_pinecone import PineconeVectorStore

from src.config import get_settings
from src.helper import download_hugging_face_embeddings
from src.prompt import system_prompt

logger = logging.getLogger(__name__)

_rag_chain: Any | None = None


def build_rag_chain():
    settings = get_settings()
    logger.info("Loading embeddings and connecting to Pinecone index '%s'", settings.pinecone_index_name)
    embeddings = download_hugging_face_embeddings()
    docsearch = PineconeVectorStore.from_existing_index(
        index_name=settings.pinecone_index_name,
        embedding=embeddings,
    )
    retriever = docsearch.as_retriever(
        search_type="similarity",
        search_kwargs={"k": settings.retrieval_k},
    )
    chat_model = ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=settings.groq_temperature,
        max_tokens=settings.groq_max_tokens,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    question_answer_chain = create_stuff_documents_chain(chat_model, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)


def init_rag_chain() -> None:
    ensure_rag_chain()


def ensure_rag_chain() -> bool:
    global _rag_chain
    if _rag_chain is not None:
        return True
    try:
        _rag_chain = build_rag_chain()
        logger.info("RAG chain ready")
        return True
    except Exception:
        logger.exception("Failed to initialize symptoms RAG chain")
        return False


def get_rag_chain():
    if not ensure_rag_chain():
        raise RuntimeError("RAG chain is not initialized")
    return _rag_chain


def is_rag_ready() -> bool:
    return _rag_chain is not None


def invoke_rag(user_message: str) -> str:
    chain = get_rag_chain()
    result = chain.invoke({"input": user_message})
    return str(result.get("answer", "")).strip()
