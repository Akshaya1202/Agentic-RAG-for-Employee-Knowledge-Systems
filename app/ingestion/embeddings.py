import os
import copy
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

    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)

    QdrantVectorStore.from_documents(
        docs,
        embedding=embeddings,
        url=os.getenv("QDRANT_URL"),
        collection_name=collection_name,
    )

    print("Documents stored in Qdrant")


def get_vector_store(collection_name="company_policies"):
    embeddings = get_embeddings()
    client = get_qdrant_client()

    return QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )


def _score_threshold():
    return float(os.getenv("MIN_VECTOR_SCORE", "0.2"))


def _metadata_filter(category):
    return qdrant_models.Filter(
        must=[
            qdrant_models.FieldCondition(
                key="metadata.category",
                match=qdrant_models.MatchValue(value=category),
            )
        ]
    )


def _attach_scores(scored_docs):
    docs = []
    for doc, score in scored_docs:
        doc_with_score = copy.copy(doc)
        doc_with_score.metadata = dict(doc.metadata)
        doc_with_score.metadata["score"] = score
        docs.append(doc_with_score)
    return docs


def _dedupe_docs(docs, k):
    seen = set()
    unique_docs = []

    for doc in docs:
        key = (
            doc.metadata.get("source"),
            doc.metadata.get("page"),
            doc.metadata.get("row"),
            " ".join(doc.page_content.split()),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)
        if len(unique_docs) >= k:
            break

    return unique_docs


def _log_retrieval(query, docs, category=None):
    print(f"Vector retrieval query={query!r} category={category!r} docs={len(docs)}")
    for index, doc in enumerate(docs, start=1):
        print(
            "  "
            f"{index}. score={doc.metadata.get('score')} "
            f"category={doc.metadata.get('category')} "
            f"source={doc.metadata.get('source')}"
        )


def _search_with_scores(vector_db, query, k, qdrant_filter=None):
    scored_docs = vector_db.similarity_search_with_score(
        query,
        k=max(k * 4, 20),
        filter=qdrant_filter,
    )
    threshold = _score_threshold()
    if threshold > 0:
        scored_docs = [(doc, score) for doc, score in scored_docs if score >= threshold]
    return _dedupe_docs(_attach_scores(scored_docs), k)


def _mmr_search(vector_db, query, k, qdrant_filter=None):
    docs = vector_db.max_marginal_relevance_search(
        query,
        k=k,
        fetch_k=max(k * 6, 30),
        lambda_mult=0.35,
        filter=qdrant_filter,
        score_threshold=_score_threshold(),
    )
    return _dedupe_docs(docs, k)


def similarity_search(query, category=None, k=5):
    vector_db = get_vector_store()

    if category:
        qdrant_filter = _metadata_filter(category)
        filtered_docs = _mmr_search(
            vector_db,
            query,
            k=k,
            qdrant_filter=qdrant_filter,
        )
        if len(filtered_docs) < max(3, k // 2):
            scored_docs = _search_with_scores(
                vector_db,
                query,
                k=k,
                qdrant_filter=qdrant_filter,
            )
            filtered_docs = _dedupe_docs(filtered_docs + scored_docs, k)
 
        if filtered_docs:
            _log_retrieval(query, filtered_docs, category)
            return filtered_docs

        # If the category slice is too narrow, fall back to a broader search.
        fallback_docs = _mmr_search(vector_db, query, k=k)
        if len(fallback_docs) < max(3, k // 2):
            fallback_docs = _dedupe_docs(
                fallback_docs + _search_with_scores(vector_db, query, k=k),
                k,
            )
        _log_retrieval(query, fallback_docs, None)
        return fallback_docs

    docs = _mmr_search(vector_db, query, k=k)
    if len(docs) < max(3, k // 2):
        docs = _dedupe_docs(
            docs + _search_with_scores(vector_db, query, k=k),
            k,
        )
    _log_retrieval(query, docs, category)
    return docs


def infer_category(query):
    q = query.lower()
    if any(word in q for word in ["fitness", "food", "cab", "wifi", "wi-fi", "telephone", "educational course", "exam fee", "benefit limit"]):
        return "benefits"
    if any(word in q for word in ["pharmacy", "tablet", "dental", "vision", "lab", "radiology", "doctor visit", "medical benefit"]):
        return "medical"
    if any(word in q for word in ["leave", "casual", "sick", "earned", "maternity", "paternity", "bereavement", "comp off", "comp-off"]):
        return "leave_policy"
    if any(word in q for word in ["travel", "reimbursement", "trip", "flight", "hotel"]):
        return "travel_policy"
    if any(word in q for word in ["salary payout", "payout date", "cutoff date", "payroll"]):
        return "payout_dates"
    if any(word in q for word in ["holiday", "republic day", "christmas", "diwali", "holi", "gandhi jayanti"]):
        return "public_holidays"
    if any(word in q for word in ["remote", "wfh", "work from home"]):
        return "wfh_policy"
    if any(word in q for word in ["attendance", "working hours", "shift", "late", "punctual"]):
        return "attendance_policy"
    return None
