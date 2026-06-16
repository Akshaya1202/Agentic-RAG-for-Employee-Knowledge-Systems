# Run Steps in Docker

1. Make sure Docker Desktop is installed and running.
2. Fill in `.env` with the required database, Qdrant, and LLM credentials.
3. Build and start the containers:
   ```bash
   docker compose up -d --build
   ```
4. Initialize the MySQL schema and load the CSV data inside the app container:
   ```bash
   docker compose exec app python -m scripts.setup_db
   ```
5. Ingest the policy PDFs into Qdrant from inside the app container:
   ```bash
   docker compose exec app python -m scripts.ingest
   ```
6. Open the app in your browser:
   ```bash
   http://localhost:8000
   ```
7. Type a question in the UI and click **Ask**.
8. To stop everything later:
   ```bash
   docker compose down
   ```
