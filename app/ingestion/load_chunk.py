import csv
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


CSV_CATEGORIES = {
    "leave_policy_dataset.csv": "leave_policy",
    "benefits.csv": "benefits",
    "medical.csv": "medical",
    "payout_dates.csv": "payout_dates",
    "public_holidays.csv": "public_holidays",
}


def load_pdfs(directory_path="app/dataset/"):
    loader = DirectoryLoader(
        path=directory_path,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} pages")
    return documents


def chunk_documents(documents, chunk_size=500, chunk_overlap=50):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    docs = splitter.split_documents(documents)
    print(f"Created {len(docs)} chunks")
    return docs


def _csv_row_to_text(file_name, row):
    if file_name == "leave_policy_dataset.csv":
        return (
            f"Leave type: {row.get('leave_type')}. "
            f"Description: {row.get('description')}. "
            f"Entitlement: {row.get('entitlement')}. "
            f"Accrual: {row.get('accrual')}. "
            f"Carry forward: {row.get('carry_forward')}. "
            f"Encashment: {row.get('encashment')}. "
            f"Remarks: {row.get('remarks')}."
        )
    if file_name == "benefits.csv":
        return (
            f"Benefit: {row.get('Benefit_Name')}. "
            f"Maximum amount: {row.get('Max_Amount_INR')} INR. "
            f"Frequency: {row.get('Frequency')}."
        )
    if file_name == "medical.csv":
        return (
            f"Medical benefit category: {row.get('Benefit_Category')}. "
            f"Category limit: {row.get('Category_Limit_INR')} INR."
        )
    if file_name == "payout_dates.csv":
        return (
            f"Payroll month: {row.get('Month')}. "
            f"Cutoff date: {row.get('Cutoff_Date')}. "
            f"Salary payout date: {row.get('Salary_Payout_Date')}."
        )
    if file_name == "public_holidays.csv":
        return (
            f"Holiday: {row.get('holiday_name')}. "
            f"Date: {row.get('holiday_date')}. "
            f"Day of week: {row.get('day_of_week')}. "
            f"Holiday type: {row.get('holiday_type')}. "
            f"Applicable states: {row.get('applicable_states')}. "
            f"Description: {row.get('description')}. "
            f"Year: {row.get('year')}."
        )
    return ". ".join(f"{key}: {value}" for key, value in row.items())


def load_csv_policy_docs(directory_path="app/dataset/"):
    docs = []
    dataset_dir = Path(directory_path)

    for csv_path in dataset_dir.glob("*.csv"):
        category = CSV_CATEGORIES.get(csv_path.name, "structured_policy")
        with csv_path.open(newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for index, row in enumerate(reader):
                docs.append(
                    Document(
                        page_content=_csv_row_to_text(csv_path.name, row),
                        metadata={
                            "source": str(csv_path),
                            "category": category,
                            "row": index,
                            "data_source": "csv",
                        },
                    )
                )

    print(f"Loaded {len(docs)} CSV policy rows")
    return docs


def add_metadata(docs):
    for doc in docs:
        source = doc.metadata.get("source", "").lower()

        if doc.metadata.get("category"):
            continue

        if "leave" in source:
            category = "leave_policy"
        elif "travel" in source:
            category = "travel_policy"
        elif "wfh" in source or "remote" in source:
            category = "wfh_policy"
        elif "attendance" in source:
            category = "attendance_policy"
        else:
            category = "general_policy"

        doc.metadata["category"] = category

    return docs


def load_and_prepare_docs(directory_path="app/dataset/"):
    documents = load_pdfs(directory_path)
    docs = chunk_documents(documents)
    docs = add_metadata(docs)
    docs.extend(load_csv_policy_docs(directory_path))
    return docs
