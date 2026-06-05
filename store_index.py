import logging

from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from src.config import get_settings
from src.helper import (
    download_hugging_face_embeddings,
    filter_to_minimal_docs,
    load_pdf_file,
    text_split,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    settings = get_settings()
    extracted_data = load_pdf_file(data="data/")
    if not extracted_data:
        raise RuntimeError("No PDF files found in data/. Add Medical_book.pdf before indexing.")

    filter_data = filter_to_minimal_docs(extracted_data)
    text_chunks = text_split(filter_data)
    logger.info("Prepared %d text chunks for indexing", len(text_chunks))

    embeddings = download_hugging_face_embeddings()
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index_name = settings.pinecone_index_name

    if not pc.has_index(index_name):
        logger.info("Creating Pinecone index '%s'", index_name)
        pc.create_index(
            name=index_name,
            dimension=384,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )

    PineconeVectorStore.from_documents(
        documents=text_chunks,
        index_name=index_name,
        embedding=embeddings,
    )
    logger.info("Indexed %d chunks into '%s'", len(text_chunks), index_name)


if __name__ == "__main__":
    main()
