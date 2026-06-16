import os

import pandas as pd
from sqlalchemy import create_engine

engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"
)

COLUMN_RENAMES = {
    "benefits": {
        "Benefit_Name": "benefit_name",
        "Max_Amount_INR": "max_amount_inr",
        "Frequency": "frequency",
    },
    "medical": {
        "Benefit_Category": "benefit_category",
        "Category_Limit_INR": "category_limit_inr",
    },
    "leave_policy": {
        "leave_type": "leave_type",
        "description": "description",
        "entitlement": "entitlement",
        "accrual": "accrual",
        "carry_forward": "carry_forward",
        "encashment": "encashment",
        "remarks": "remarks",
    },
    "payout_dates": {
        "Month": "month_name",
        "Cutoff_Date": "cutoff_date",
        "Salary_Payout_Date": "salary_payout_date",
    },
    "public_holidays": {
        "id": "id",
        "holiday_name": "holiday_name",
        "holiday_date": "holiday_date",
        "day_of_week": "day_of_week",
        "holiday_type": "holiday_type",
        "applicable_states": "applicable_states",
        "description": "description",
        "year": "year",
    },
}


def load_csv(file_path, table_name):
    df = pd.read_csv(file_path)
    df = df.rename(columns=COLUMN_RENAMES.get(table_name, {}))

    for column in df.columns:
        if "date" in column.lower():
            df[column] = pd.to_datetime(df[column]).dt.date

    for column in ["id", "max_amount_inr", "category_limit_inr", "year"]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").astype("Int64")

    df.to_sql(
        table_name,
        con=engine,
        if_exists="replace",
        index=False,
    )

    print(f"{table_name} data inserted")
