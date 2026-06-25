import os
import re
from datetime import date
from sqlalchemy import create_engine, text
from app.llm.gemini import get_model

engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"
)

def query_mysql(question):
    llm = get_model()

    prompt = f"""
    Convert to a MySQL query using only the tables and columns that exist in this database.
    Only output SQL. Do not wrap it in markdown fences.
    Prefer a single SELECT statement. Never use INSERT, UPDATE, DELETE, DROP, ALTER, or CREATE.
    Return the most useful field for the user question, not the primary key unless the user explicitly asks for an id.
    If the user asks whether something is a holiday, query public_holidays.
    If the user asks about leave type, entitlement, carry forward, encashment, or remarks, query leave_policy.
    If the user asks about a benefit amount or limit, query benefits or medical.
    If the user mentions a date like "25th Dec" or "tomorrow", convert it into a SQL date comparison.
    If the user asks about counts, use COUNT(*).

    Available tables:
    - public_holidays(id, holiday_name, holiday_date, day_of_week, holiday_type, applicable_states, description, year)
    - leave_policy(id, leave_type, description, entitlement, accrual, carry_forward, encashment, remarks)
    - benefits(id, benefit_name, max_amount_inr, frequency)
    - medical(id, benefit_category, category_limit_inr)
    - payout_dates(id, month_name, cutoff_date, salary_payout_date)

    Today is {date.today().isoformat()}.

    Question: {question}
    """

    sql = llm.invoke(prompt).content.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    sql = sql.strip()

    with engine.connect() as conn:
        try:
            result = conn.execute(text(sql))
            rows = result.fetchall()
            if rows:
                return rows
        except Exception:
            pass
