from langchain.agents import create_agent
from app.llm.gemini import get_model

def route_query(query):
    model = get_model(temperature=0)
    agent = create_agent(
        model=model,
        tools=[],
        system_prompt="""
        You are a router agent.

        Analyze the user's question carefully and choose the best data source.

        Use SQL when the answer is likely to be:
        - numeric or quantifiable
        - a count, total, sum, amount, date, limit, entitlement, or specific table value
        - something that can be answered from structured records

        Use VECTOR when the answer is likely to be:
        - explanatory or policy-based
        - written in a document or PDF
        - about rules, guidelines, procedures, or descriptions

        Output ONLY one word: SQL or VECTOR

        Examples:
        - "How many public holidays are there?" -> SQL
        - "What is the casual leave entitlement?" -> SQL
        - "What is the maximum medical allowance?" -> SQL
        - "Explain the company's remote work policy." -> VECTOR
        - "What does the travel policy say about reimbursement?" -> VECTOR
        """
    )
    response = agent.invoke({
        "messages": [{"role": "user", "content": query}]
    })
    output = response["messages"][-1].content.strip().upper()
    return "SQL" if "SQL" in output else "VECTOR"
