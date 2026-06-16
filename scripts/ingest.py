from app.ingestion.embeddings import store_documents
from app.ingestion.load_chunk import load_and_prepare_docs

docs = load_and_prepare_docs()
store_documents(docs)
