import os
import re
from datetime import date

from sqlalchemy import create_engine, text

from app.llm.gemini import get_model


engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"
)


ENTITY_SPECS = [
    {
        "table": "leave_policy",
        "name_column": "leave_type",
        "select_columns": ["leave_type"],
    },
    {
        "table": "benefits",
        "name_column": "benefit_name",
        "select_columns": ["benefit_name", "max_amount_inr", "frequency"],
    },
    {
        "table": "medical",
        "name_column": "benefit_category",
        "select_columns": ["benefit_category", "category_limit_inr"],
    },
    {
        "table": "public_holidays",
        "name_column": "holiday_name",
        "select_columns": [
            "holiday_name",
            "holiday_date",
            "day_of_week",
            "holiday_type",
            "applicable_states",
        ],
    },
    {
        "table": "payout_dates",
        "name_column": "month_name",
        "select_columns": ["month_name", "cutoff_date", "salary_payout_date"],
    },
]


def _normalize(value):
    normalized = value.lower().replace("-", " ")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def _tokens(value):
    tokens = _normalize(value).split()
    return [token[:-1] if token.endswith("s") and len(token) > 3 else token for token in tokens]


def _contains_token_sequence(query_tokens, entity_tokens):
    if not entity_tokens or len(entity_tokens) > len(query_tokens):
        return False

    for start in range(0, len(query_tokens) - len(entity_tokens) + 1):
        if query_tokens[start : start + len(entity_tokens)] == entity_tokens:
            return True

    return False


def _run_select(sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return [dict(row) for row in result.mappings().all()]


def _load_entity_candidates():
    candidates = []
    with engine.connect() as conn:
        for spec in ENTITY_SPECS:
            rows = conn.execute(
                text(f"SELECT DISTINCT {spec['name_column']} AS name FROM {spec['table']}")
            ).mappings().all()
            for row in rows:
                if row["name"]:
                    candidates.append({**spec, "name": row["name"]})
    return candidates


def _find_entity(question):
    query_tokens = _tokens(question)
    matches = []

    for candidate in _load_entity_candidates():
        entity_tokens = _tokens(candidate["name"])
        if _contains_token_sequence(query_tokens, entity_tokens):
            matches.append((len(entity_tokens), candidate))

    if not matches:
        return None

    return sorted(matches, key=lambda item: item[0], reverse=True)[0][1]


def _field_for_leave_question(question):
    q = _normalize(question)
    if any(word in q for word in ["encash", "encashable", "encashment"]):
        return "encashment"
    if any(word in q for word in ["carry forward", "carried forward", "carry forward"]):
        return "carry_forward"
    if any(word in q for word in ["accrual", "accrue"]):
        return "accrual"
    if any(word in q for word in ["remark", "note"]):
        return "remarks"
    return "entitlement"


def _columns_for_entity(question, entity):
    columns = list(entity["select_columns"])

    if entity["table"] == "leave_policy":
        field = _field_for_leave_question(question)
        if field not in columns:
            columns.append(field)
        if "description" not in columns:
            columns.append("description")

    return columns


def _format_frequency(value):
    if not value:
        return ""
    return str(value).strip().lower()


def _format_structured_answer(question, sql, rows):
    if not rows:
        return "I could not find a matching record in the structured policy data."

    row = rows[0]
    q = _normalize(question)

    if "leave_type" in row:
        leave_type = row.get("leave_type")
        if "encashment" in row and any(word in q for word in ["encash", "encashable", "encashment"]):
            encashment = str(row.get("encashment", "")).strip()
            prefix = "Yes" if encashment.lower() in {"yes", "y", "true"} else "No"
            return f"{prefix}, {leave_type.lower()} is {'encashable' if prefix == 'Yes' else 'not encashable'}."
        if "policy" in q and leave_type == "Maternity Leave":
            return "Maternity leave is provided as per statutory laws for female employees."
        if "carry_forward" in row and "carry forward" in q:
            return f"{leave_type} carry-forward: {row.get('carry_forward')}."
        if "accrual" in row and any(word in q for word in ["accrual", "accrue"]):
            return f"{leave_type} accrual: {row.get('accrual')}."
        if "entitlement" in row:
            return f"Employees are provided {row.get('entitlement')} of {leave_type.lower()}."

    if "benefit_name" in row:
        benefit = row.get("benefit_name")
        amount = row.get("max_amount_inr")
        frequency = _format_frequency(row.get("frequency"))
        suffix = f" {frequency}" if frequency else ""
        return f"The maximum amount for {benefit} benefit is {amount} INR{suffix}."

    if "benefit_category" in row:
        category = row.get("benefit_category")
        amount = row.get("category_limit_inr")
        return f"The category limit for {category} under medical benefits is {amount} INR."

    if "month_name" in row:
        if "cutoff_date" in row and "cutoff" in q:
            return f"The cutoff date for {row.get('month_name')} is {row.get('cutoff_date')}."
        if "salary_payout_date" in row:
            return f"The salary payout date for {row.get('month_name')} is {row.get('salary_payout_date')}."

    if "holiday_name" in row:
        if "applicable_states" in row and any(word in q for word in ["state", "states", "applicable"]):
            return f"{row.get('holiday_name')} is applicable in {row.get('applicable_states')}."
        if "day_of_week" in row and any(word in q for word in ["day", "week"]):
            return f"{row.get('holiday_name')} is on a {row.get('day_of_week')}."
        if "holiday_type" in row and any(word in q for word in ["type", "restricted", "national", "regional"]):
            return f"{row.get('holiday_name')} is a {row.get('holiday_type')} holiday."
        if "holiday_date" in row:
            day = f" ({row.get('day_of_week')})" if row.get("day_of_week") else ""
            return f"{row.get('holiday_name')} is on {row.get('holiday_date')}{day}."

    fields = ", ".join(f"{key}: {value}" for key, value in row.items())
    return fields


def deterministic_query(question):
    entity = _find_entity(question)
    if not entity:
        return None

    columns = _columns_for_entity(question, entity)
    sql = (
        f"SELECT {', '.join(columns)} "
        f"FROM {entity['table']} "
        f"WHERE LOWER({entity['name_column']}) = LOWER(:entity_name)"
    )
    rows = _run_select(sql, {"entity_name": entity["name"]})
    return sql, rows, _format_structured_answer(question, sql, rows)


def _value_catalog_for_prompt():
    grouped = {}
    for candidate in _load_entity_candidates():
        grouped.setdefault(candidate["table"], []).append(str(candidate["name"]))

    return "\n".join(
        f"    - {table} values: {', '.join(values)}"
        for table, values in grouped.items()
    )


def _clean_sql(sql):
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()


def _validate_select(sql):
    sql_clean = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql_clean = re.sub(r"--.*$", "", sql_clean, flags=re.MULTILINE).strip()

    if not sql_clean.upper().startswith("SELECT"):
        raise ValueError(f"Unsafe SQL generated: SQL query does not start with SELECT. Query: {sql}")

    unsafe_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE", "TRUNCATE"]
    for keyword in unsafe_keywords:
        if re.search(r"\b" + keyword + r"\b", sql_clean, re.IGNORECASE):
            raise ValueError(f"Unsafe SQL generated: contains forbidden keyword {keyword}. Query: {sql}")


def query_mysql(question):
    deterministic = deterministic_query(question)
    if deterministic:
        return deterministic

    llm = get_model()
    value_catalog = _value_catalog_for_prompt()

    prompt = f"""
    Convert to a MySQL query using only the tables and columns that exist in this database.
    Only output SQL. Do not wrap it in markdown fences.
    Prefer a single SELECT statement. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
    Return the most useful field for the user question, not the primary key unless the user explicitly asks for an id.
    If the user asks whether something is a holiday, query public_holidays.
    If the user asks about leave type, entitlement, carry forward, encashment, or remarks, query leave_policy.
    If the user asks about a benefit amount or limit, query benefits or medical.
    If the user mentions a date like "25th Dec" or "tomorrow", convert it into a SQL date comparison.
    Use COUNT(*) only when the user asks how many records/items exist.
    Do not use COUNT(*) for questions like "how many days of sick leave"; those ask for entitlement.
    For leave days, select leave_type and entitlement.
    For benefit limits, select benefit_name, max_amount_inr, and frequency from benefits.
    For medical category limits, select benefit_category and category_limit_inr from medical.
    Match names case-insensitively with LOWER(...) or LIKE when needed.

    Available tables:
    - public_holidays(id, holiday_name, holiday_date, day_of_week, holiday_type, applicable_states, description, year)
    - leave_policy(id, leave_type, description, entitlement, accrual, carry_forward, encashment, remarks)
    - benefits(id, benefit_name, max_amount_inr, frequency)
    - medical(id, benefit_category, category_limit_inr)
    - payout_dates(id, month_name, cutoff_date, salary_payout_date)

    Current database values:
{value_catalog}

    Today is {date.today().isoformat()}.

    Question: {question}
    """

    sql = _clean_sql(llm.invoke(prompt).content.strip())
    _validate_select(sql)

    try:
        rows = _run_select(sql)
        answer = _format_structured_answer(question, sql, rows)
        return sql, rows, answer
    except Exception as e:
        print(f"Database error executing query '{sql}': {e}")
        raise e
