"""
Index PDF(s) from a folder into a Pinecone index (for mental health or future lab RAG).

Examples:
  python store_index_to_pinecone.py --folder data/kb/mental_health --index medical-chatbot-mh
  python store_index_to_pinecone.py --folder data/kb/lab_results --index medical-chatbot-lab

Requires .env with PINECONE_API_KEY (and GROQ_API_KEY for Settings loader).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from src.config import get_settings
from src.helper import (
    download_hugging_face_embeddings,
    filter_to_minimal_docs,
    text_split,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_pdfs_from_folder(folder: Path):
    loader = DirectoryLoader(
        str(folder),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        recursive=True,
    )
    return loader.load()


def ensure_index(pc: Pinecone, index_name: str) -> None:
    if not pc.has_index(index_name):
        logger.info("Creating Pinecone index '%s' (384-dim, cosine)", index_name)
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Index PDFs into a Pinecone index")
    parser.add_argument(
        "--folder",
        required=True,
        help="Folder containing PDF files (e.g. data/kb/mental_health)",
    )
    parser.add_argument(
        "--index",
        required=True,
        help="Pinecone index name (e.g. medical-chatbot-mh)",
    )
    parser.add_argument(
        "--namespace",
        default="",
        help="Optional Pinecone namespace (for future multi-namespace setup)",
    )
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")

    settings = get_settings()
    extracted = load_pdfs_from_folder(folder)
    if not extracted:
        raise SystemExit(f"No PDF files found under {folder}")

    logger.info("Loaded %d PDF page document(s) from %s", len(extracted), folder)
    chunks = text_split(filter_to_minimal_docs(extracted))
    logger.info("Prepared %d chunks", len(chunks))

    embeddings = download_hugging_face_embeddings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    ensure_index(pc, args.index)

    kwargs: dict = {
        "documents": chunks,
        "index_name": args.index,
        "embedding": embeddings,
    }
    if args.namespace.strip():
        kwargs["namespace"] = args.namespace.strip()

    PineconeVectorStore.from_documents(**kwargs)
    logger.info(
        "Indexed %d chunks into index '%s'%s",
        len(chunks),
        args.index,
        f" namespace '{args.namespace}'" if args.namespace.strip() else "",
    )


if __name__ == "__main__":
    main()
