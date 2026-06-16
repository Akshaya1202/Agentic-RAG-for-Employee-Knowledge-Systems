# Company Policies RAG

A Retrieval-Augmented Generation (RAG) system that answers company policy questions using a hybrid approach combining semantic search and SQL queries.

## Overview

This project implements an intelligent Q&A system for company policies that leverages:

- **Vector Database** (Qdrant) for semantic similarity search over policy documents
- **SQL Database** (MySQL) for structured policy data and metadata
- **LLM** (Google Gemini) for intelligent query understanding and answer generation
- **Hybrid Router** that intelligently routes queries to SQL or semantic search based on question type

## Features

- 📚 **Multi-source Retrieval**: Combines structured data (SQL) and unstructured documents (Vector DB)
- 🧠 **Smart Category Inference**: Automatically categorizes queries (leave, travel, attendance, WFH, etc.)
- 🔀 **Hybrid Routing**: Routes queries to SQL for structured data or semantic search for policies
- 🚀 **Fast Semantic Search**: Uses FastEmbed for efficient vector embeddings
- 🐳 **Containerized**: Docker setup for easy deployment
- 💬 **Interactive CLI**: Ask questions about company policies in natural language

## Tech Stack

- **Backend**: Python, FastAPI, Uvicorn
- **LLM**: LangChain, Google Gemini API
- **Vector Database**: Qdrant, FastEmbed (BAAI/bge-small-en-v1.5)
- **SQL Database**: MySQL, SQLAlchemy
- **Data Processing**: Pandas, PyPDF
- **DevOps**: Docker, Docker Compose

## Project Structure

```
├── app/
│   ├── main.py                 # CLI entry point
│   ├── agents/
│   │   ├── hybrid_agents.py    # Query routing & answer generation
│   │   └── router.py           # Query classification logic
│   ├── db/
│   │   ├── init_db.py          # Database initialization
│   │   ├── load_csv_to_sql.py  # Load CSV data to MySQL
│   │   └── mysql_query.py      # SQL query generation via LLM
│   ├── ingestion/
│   │   ├── embeddings.py       # Vector store & semantic search
│   │   └── load_chunk.py       # Document chunking
│   ├── llm/
│   │   └── gemini.py           # LLM initialization
│   └── static/                 # Web UI (HTML, CSS, JS)
├── dataset/                    # CSV files with policy data
├── scripts/
│   ├── setup_db.py            # Initialize DB & load CSVs
│   └── ingest.py              # Ingest documents to Qdrant
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Installation

### Prerequisites

- Docker & Docker Compose installed
- Python 3.9+ (for local development)
- Google Gemini API key

### Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd "Company policies RAG"
   ```

2. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in:
   - `GEMINI_API_KEY`: Get from [Google AI Studio](https://aistudio.google.com/apikey)
   - Database credentials (already configured for Docker)
   - Qdrant URL (already configured for Docker)

3. **Build and start containers**

   ```bash
   docker compose up -d --build
   ```

4. **Initialize the database**

   ```bash
   docker compose exec app python -m scripts.setup_db
   ```

   This creates the MySQL schema and loads CSV policy data.

5. **Ingest documents into vector store**
   ```bash
   docker compose exec app python -m scripts.ingest
   ```

## Usage

### Interactive CLI

Once setup is complete, run:

```bash
docker compose exec app python -m app.main
```

Then ask questions:

```
Ask: What is the leave policy for casual leave?
Ask: When is the next salary payout?
Ask: Am I eligible for maternity leave?
Ask: exit
```

### Web UI (API Available)

The FastAPI server (currently serving on port 8000) can be enabled by uncommenting the API code in `app/main.py`.

## Query Examples

The system handles various types of queries:

**Leave Policy Questions**

- "How many casual leave days am I entitled to?"
- "What is the maternity leave policy?"

**Travel & Reimbursement**

- "What is the reimbursement limit for flights?"

**Attendance**

- "What are the working hours?"
- "When can I take comp-off?"

**Remote Work**

- "Can I work from home on Fridays?"

## How It Works

1. **Query Classification** (`router.py`):
   - Determines if query should be answered via SQL or semantic search
   - SQL queries: For structured data (dates, counts, eligibility checks)
   - Semantic search: For policy details and descriptions

2. **Category Inference** (`embeddings.py`):
   - Infers policy category from query keywords
   - Categories: leave_policy, travel_policy, wfh_policy, attendance_policy

3. **Data Retrieval**:
   - **SQL Route**: Generates SQL queries using LLM, executes on MySQL
   - **Semantic Route**: Retrieves similar documents from Qdrant vector store

4. **Answer Generation**:
   - Uses Google Gemini LLM to generate coherent, factual answers
   - Grounds answers in retrieved context to avoid hallucinations

## Database Schema

### MySQL Tables

- `public_holidays`: Holiday dates and types
- `leave_policy`: Leave types, entitlements, carry-forward policies
- `benefits`: Benefit amounts and limits
- `medical`: Medical benefit coverage limits
- `payout_dates`: Salary payout schedule

### Qdrant Collections

- `company_policies`: Vector embeddings of policy documents with metadata

## Environment Variables

See `.env.example` for all required variables:

- `GEMINI_API_KEY`: Google Gemini API key
- `QDRANT_URL`: Qdrant server URL
- `DB_HOST`: MySQL host
- `DB_USER`: MySQL username
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: MySQL database name
