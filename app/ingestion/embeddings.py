import os
from langchain_qdrant import QdrantVectorStore
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from qdrant_client.http import models as qdrant_models
from qdrant_client import QdrantClient


def get_embeddings():
    return FastEmbedEmbeddings(
        model_name="BAAI/bge-small-en-v1.5"
    )


def get_qdrant_client():
    return QdrantClient(
        url=os.getenv("QDRANT_URL")
    )


def store_documents(docs, collection_name="company_policies"):
    embeddings = get_embeddings()
    client = get_qdrant_client()

    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    vector_store.add_documents(docs)

    print("Documents stored in Qdrant")


def get_vector_store(collection_name="company_policies"):
    embeddings = get_embeddings()
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )


def similarity_search(query, category=None, k=5):
    vector_db = get_vector_store()

    if category:
        qdrant_filter = qdrant_models.Filter(
            must=[
                qdrant_models.FieldCondition(
                    key="category",
                    match=qdrant_models.MatchValue(value=category),
                )
            ]
        )
        filtered_docs = vector_db.similarity_search(
            query,
            k=k,
            filter=qdrant_filter
        )
        if filtered_docs:
            return filtered_docs

        # If the category slice is too narrow, fall back to a broader search.
        return vector_db.similarity_search(query, k=k)

    return vector_db.similarity_search(query, k=k)


def infer_category(query):
    q = query.lower()
    if any(word in q for word in ["leave", "casual", "sick", "earned", "maternity", "paternity", "bereavement", "comp off", "comp-off"]):
        return "leave_policy"
    if any(word in q for word in ["travel", "reimbursement", "trip", "flight", "hotel"]):
        return "travel_policy"
    if any(word in q for word in ["remote", "wfh", "work from home"]):
        return "wfh_policy"
    if any(word in q for word in ["attendance", "working hours", "shift", "late", "punctual"]):
        return "attendance_policy"
    return None
