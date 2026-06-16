from app.db.init_db import init_db
from app.db.load_csv_to_sql import load_csv

init_db()

load_csv("app/dataset/benefits.csv", "benefits")
load_csv("app/dataset/medical.csv", "medical")
load_csv("app/dataset/leave_policy_dataset.csv", "leave_policy")
load_csv("app/dataset/payout_dates.csv", "payout_dates")
load_csv("app/dataset/public_holidays.csv", "public_holidays")