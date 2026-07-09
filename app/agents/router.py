from langchain.agents import create_agent
from app.llm.gemini import get_model

import re


VECTOR_INTENT_PATTERNS = [
    r"^how\s+do\b",
    r"^how\s+does\b",
    r"\bhow\s+(?:can|should|do|does)\b.*\b(?:request|apply|book|report|submit|raise)\b",
    r"\bprocedure\b",
    r"\bprocess\b",
    r"\bpolicy\b",
    r"\bexplain\b",
    r"\bwhat\s+happens\b",
    r"\bwhat\s+constitutes\b",
    r"\bwho\s+is\s+responsible\b",
    r"\ballowed\b",
    r"\brequires?\s+(?:approval|special approval)\b",
]

SQL_INTENT_PATTERNS = [
    r"\bhow many\s+(?:days|public holidays|holidays|records|items)\b",
    r"\bentitlement\b",
    r"\bencash(?:ment|able)?\b",
    r"\bcarry[- ]?forward\b",
    r"\baccrual\b",
    r"\bmaximum\b",
    r"\bamount\b",
    r"\blimits?\b",
    r"\bcap(?:ped)?\b",
    r"\bclaim(?:ed)?\b",
    r"\bpayout\b",
    r"\bcutoff\b",
    r"\bpayroll\b",
    r"\bholiday type\b",
    r"\brestricted or national\b",
    r"\bday of the week\b",
    r"\bwhen is\b",
    r"\bwhat day\b",
]


def route_query(query):
    q = query.lower()
    if any(re.search(pattern, q) for pattern in VECTOR_INTENT_PATTERNS):
        return "VECTOR"
    if any(re.search(pattern, q) for pattern in SQL_INTENT_PATTERNS):
        return "SQL"

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
