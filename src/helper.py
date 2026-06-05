import threading
from typing import List

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config import get_settings


def load_pdf_file(data: str):
    loader = DirectoryLoader(
        data,
        glob="*.pdf",
        loader_cls=PyPDFLoader,
    )
    return loader.load()


def filter_to_minimal_docs(docs: List[Document]) -> List[Document]:
    minimal_docs: List[Document] = []
    for doc in docs:
        src = doc.metadata.get("source")
        minimal_docs.append(
            Document(
                page_content=doc.page_content,
                metadata={"source": src},
            )
        )
    return minimal_docs


def text_split(extracted_data):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=20)
    return text_splitter.split_documents(extracted_data)


_embeddings_lock = threading.Lock()
_shared_embeddings: HuggingFaceEmbeddings | None = None


def download_hugging_face_embeddings():
    """Return a process-wide shared embedding model (loads once under lazy RAG)."""
    global _shared_embeddings
    if _shared_embeddings is not None:
        return _shared_embeddings
    with _embeddings_lock:
        if _shared_embeddings is None:
            settings = get_settings()
            _shared_embeddings = HuggingFaceEmbeddings(
                model_name=settings.embedding_model,
            )
        return _shared_embeddings


def reset_shared_embeddings_cache() -> None:
    global _shared_embeddings
    with _embeddings_lock:
        _shared_embeddings = None
