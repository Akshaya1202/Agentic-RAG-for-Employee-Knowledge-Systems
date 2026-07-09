from app.agents.router import route_query
from app.ingestion.embeddings import infer_category, similarity_search
from app.db.mysql_query import query_mysql
from app.llm.gemini import get_model

class SQLDocument:
    def __init__(self, page_content: str, metadata=None):
        self.page_content = page_content
        self.metadata = metadata or {}

def run_query(query):
    route = route_query(query)

    if route == "SQL":
        sql_query, rows, answer = query_mysql(query)
        mock_doc = SQLDocument(
            f"Executed SQL Query: {sql_query}\nDatabase Result: {rows}",
            metadata={"source": "mysql", "route": "SQL", "sql": sql_query, "rows": rows},
        )
        return {
            "answer": answer,
            "documents": [mock_doc],
            "route": "SQL",
            "sql": sql_query,
            "rows": rows,
        }

    else:
        category = infer_category(query)
        docs = similarity_search(query, category=category, k=8)
        context = "\n\n".join([d.page_content for d in docs])
        llm = get_model()

        prompt = f"""
        You are answering a question using retrieved policy context.
        Use only the facts in the context below, but synthesize across all retrieved chunks.
        Prefer the most specific sentence that answers the user's question.
        If a rule requires approval, conditions, exceptions, or a named workflow, include those details.
        If the context only partially answers the question, answer with the partial facts and say what is missing.
        Say you could not find it only when none of the retrieved context is relevant.
        Keep the answer concise and factual.

        Context:
        {context}

        Question: {query}
        """

        answer = llm.invoke(prompt).content
        return {
            "answer": answer,
            "documents": docs,
            "route": "VECTOR",
            "category": category,
            "retrieval": [
                {
                    "source": d.metadata.get("source"),
                    "category": d.metadata.get("category"),
                    "score": d.metadata.get("score"),
                }
                for d in docs
            ],
        }
