import os
from sqlalchemy import create_engine, text

engine = create_engine(
    f"mysql+mysqlconnector://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:3306/{os.getenv('DB_NAME')}"
)

def init_db():
    with engine.connect() as conn:

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS benefits (
            id INT AUTO_INCREMENT PRIMARY KEY,
            benefit_name VARCHAR(255),
            max_amount_inr INT,
            frequency VARCHAR(50)
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS medical (
            id INT AUTO_INCREMENT PRIMARY KEY,
            benefit_category VARCHAR(255),
            category_limit_inr INT
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS leave_policy (
            id INT AUTO_INCREMENT PRIMARY KEY,
            leave_type VARCHAR(255),
            description TEXT,
            entitlement VARCHAR(100),
            accrual VARCHAR(100),
            carry_forward VARCHAR(100),
            encashment VARCHAR(50),
            remarks TEXT
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS payout_dates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            month_name VARCHAR(20),
            cutoff_date DATE,
            salary_payout_date DATE
        )
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS public_holidays (
            id INT PRIMARY KEY,
            holiday_name VARCHAR(255),
            holiday_date DATE,
            day_of_week VARCHAR(50),
            holiday_type VARCHAR(50),
            applicable_states VARCHAR(255),
            description TEXT,
            year INT
        )
        """))

        conn.commit()
