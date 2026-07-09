from app.agents.hybrid_agents import run_query


CASES = [
    ("How many days of sick leave are provided?", ["10 days per year"]),
    ("What is the maximum reimbursement limit for Fitness benefits?", ["25000", "per year"]),
    ("How much can be claimed for Cab expenses per month?", ["4000", "per month"]),
    ("What is the monthly WiFi benefit limit?", ["1500", "per month"]),
    ("What is the Telephone benefit limit?", ["1000", "per month"]),
    ("Are bereavement leaves encashable?", ["no", "not encashable"]),
    ("How do employees request casual leave?", ["HR portal", "manager"]),
    ("Is remote work allowed from other countries?", ["HR", "legal", "tax"]),
]


def main():
    failures = []

    for question, expected_terms in CASES:
        response = run_query(question)
        answer = response.get("answer", "")
        normalized_answer = answer.lower()

        missing_terms = [
            term for term in expected_terms if term.lower() not in normalized_answer
        ]

        print(f"Question: {question}")
        print(f"Route: {response.get('route')}")
        print(f"Answer: {answer}")
        if response.get("sql"):
            print(f"SQL: {response.get('sql')}")
            print(f"Rows: {response.get('rows')}")
        print("-" * 60)

        if missing_terms:
            failures.append((question, answer, missing_terms))

    if failures:
        print("Regression failures:")
        for question, answer, missing_terms in failures:
            print(f"- {question}")
            print(f"  Answer: {answer}")
            print(f"  Missing terms: {missing_terms}")
        raise SystemExit(1)

    print("All regression checks passed.")


if __name__ == "__main__":
    main()
