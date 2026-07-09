from app.agents.router import route_query
from app.ingestion.embeddings import infer_category, similarity_search
from app.db.mysql_query import query_mysql
from app.llm.gemini import get_model

class SQLDocument:
    def __init__(self, page_content: str):
        self.page_content = page_content

def run_query(query):
    route = route_query(query)

    if route == "SQL":
        sql_query, result = query_mysql(query)
        mock_doc = SQLDocument(f"Executed SQL Query: {sql_query}\nDatabase Result: {result}")
        return {"answer": str(result), "documents": [mock_doc]}

    else:
        category = infer_category(query)
        docs = similarity_search(query, category=category, k=8)
        context = "\n\n".join([d.page_content for d in docs])
        llm = get_model()

        prompt = f"""
        You are answering a question using retrieved policy context.
        Use only the facts in the context below.
        If the context does not contain the answer, say you could not find it in the provided documents.
        Keep the answer concise and factual.

        {context}

        Question: {query}
        """

        answer = llm.invoke(prompt).content
        return {"answer": answer, "documents": docs}


