from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


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


def add_metadata(docs):
    for doc in docs:
        source = doc.metadata.get("source", "").lower()

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
    return docs
