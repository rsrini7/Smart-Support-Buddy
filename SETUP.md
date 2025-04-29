# Support Buddy - Setup Guide

## Prerequisites
- Python 3.11+
- uv (https://github.com/astral-sh/uv) for Python dependency management
  - Install with `pip install uv` or `brew install uv`
- Node.js and npm
- Docker and Docker Compose (for containerized setup)
- Jira instance (local or cloud)
- Confluence instance (local, via Docker Compose)
- Internet access for StackOverflow Q&A ingestion
- PostgreSQL (or use containerized version)

## Development Setup
1. Clone this repository
2. Install backend dependencies (Python 3.11 recommended):
   ```bash
   ./start_backend.sh
   ```
   - This script will create a `.venv` using `uv`, and install dependencies from `pyproject.toml` via `uv sync`.
   - You do NOT need to manage `requirements.txt` anymore. All dependencies are managed in `pyproject.toml`.
   - To add or update dependencies, edit `pyproject.toml` and run `uv sync`.
3. Configure environment variables (see Environment Variables section)
   - For **Confluence Server**, set these in `backend/.env`:
     ```env
     CONFLUENCE_USERNAME=your-confluence-username
     CONFLUENCE_PASSWORD=your-confluence-password
     ```
   - For **Jira**, use:
     ```env
     JIRA_USERNAME=your-jira-username
     JIRA_PASSWORD=your-jira-password      # For local/server instance
     JIRA_API_TOKEN=          # For cloud instance
     ```
4. Start the services:
   - Development mode:
     ```bash
     ./start_backend.sh  # Starts backend with auto-reload
     ./start_frontend.sh  # Starts frontend dev server
     ```
   - Production mode:
     ```bash
     ./start_backend.sh --no-reload --host 0.0.0.0
     ./start_frontend.sh
     ```

## Vector Database Configuration

Support Buddy can use either ChromaDB or FAISS as its vector database backend.

*   **ChromaDB (Default):** Uses a persistent ChromaDB instance. The data is stored in the directory specified by the `VECTOR_DB_PATH` environment variable (defaults to `./data/chroma`). You can also run ChromaDB as a separate server and connect via HTTP by setting `CHROMA_USE_HTTP=true`.
*   **FAISS (Alternative):** Uses a local FAISS index for vector storage. To enable FAISS, set the environment variable `USE_FAISS=true`. The FAISS index files will be stored in the directory specified by the `FAISS_INDEX_PATH` environment variable (defaults to `./data/faiss`).

**Switching:**

To switch between databases, modify the relevant environment variables (e.g., in your `.env` file or export them) before starting the backend application.

Example `.env` for FAISS:
```dotenv
USE_FAISS=true
# FAISS_INDEX_PATH=./data/my_faiss_index # Optional: Override default path
```

Example `.env` for ChromaDB (Persistent Client):
```dotenv
# USE_FAISS=false # Or simply omit USE_FAISS
VECTOR_DB_PATH=./data/my_chroma_db # Optional: Override default path
```

Example `.env` for ChromaDB (HTTP Client):
```dotenv
# USE_FAISS=false
CHROMA_USE_HTTP=true
# CHROMA_HTTP_HOST=your_chroma_server # Optional: Specify host if not localhost
# CHROMA_HTTP_PORT=8000 # Optional: Specify port if not 8000
```

**Note:** Ensure the required dependencies are installed. `faiss-cpu` is needed for FAISS support (included in `pyproject.toml`).

### Docker Usage
- The backend Dockerfile now uses `uv sync` and `pyproject.toml` for dependency management. No need for `requirements.txt`.
- Example build and run:
  ```bash
  docker build -t support-buddy-backend ./backend
  docker run --env-file ./backend/.env -p 8000:8000 support-buddy-backend
  ```

### Notes
- The `.venv/` directory is now the standard location for the Python virtual environment (see `.gitignore`).
- All Python dependencies are managed in `pyproject.toml` and installed with `uv sync` (see [start_backend.sh](./start_backend.sh) and [backend/Dockerfile](./backend/Dockerfile)).

## Starting the Frontend

To start the frontend React application, use the provided script:
```sh
./start_frontend.sh
```

## Activating the Backend Python Virtual Environment

To activate the backend's Python virtual environment, use the provided script:
```sh
# For Linux/macOS (bash/zsh)
source ./set_venv.sh
```

For Windows (PowerShell), open PowerShell as Administrator (if needed for execution policy) and run:

```powershell
# Make sure execution policy allows running local scripts
# You might need to run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
. .\set_venv.ps1
```

## Environment Variables
The backend requires a `.env` file with configuration for:
```env
# Jira Settings
JIRA_URL=http://localhost:9090
JIRA_USERNAME=admin
JIRA_PASSWORD=admin      # For local/server instance
JIRA_API_TOKEN=          # For cloud instance
# Confluence Settings
CONFLUENCE_USERNAME=your-confluence-username
CONFLUENCE_PASSWORD=your-confluence-password
# Vector DB Settings
VECTOR_DB_PATH=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# (No special StackOverflow credentials required for public Q&A ingestion)
```

## Vector Database Configuration

Support Buddy can use either ChromaDB or FAISS as its vector database backend.

*   **ChromaDB (Default):** Uses a persistent ChromaDB instance. The data is stored in the directory specified by the `VECTOR_DB_PATH` environment variable (defaults to `./data/chroma`). You can also run ChromaDB as a separate server and connect via HTTP by setting `CHROMA_USE_HTTP=true`.
*   **FAISS (Alternative):** Uses a local FAISS index for vector storage. To enable FAISS, set the environment variable `USE_FAISS=true`. The FAISS index files will be stored in the directory specified by the `FAISS_INDEX_PATH` environment variable (defaults to `./data/faiss`).

**Switching:**

To switch between databases, modify the relevant environment variables (e.g., in your `.env` file or export them) before starting the backend application.

Example `.env` for FAISS:

```dotenv
USE_FAISS=true
# FAISS_INDEX_PATH=./data/my_faiss_index # Optional: Override default path
```

Example `.env` for ChromaDB (Persistent Client):

```dotenv
# USE_FAISS=false # Or simply omit USE_FAISS
VECTOR_DB_PATH=./data/my_chroma_db # Optional: Override default path
```

Example `.env` for ChromaDB (HTTP Client):

```dotenv
# USE_FAISS=false
CHROMA_USE_HTTP=true
# CHROMA_HTTP_HOST=your_chroma_server # Optional: Specify host if not localhost
# CHROMA_HTTP_PORT=8000 # Optional: Specify port if not 8000
```

**Note:** Ensure the required dependencies are installed. `faiss-cpu` is needed for FAISS support (included in `pyproject.toml`).

### Docker Usage
- The backend Dockerfile now uses `uv sync` and `pyproject.toml` for dependency management. No need for `requirements.txt`.
- Example build and run:
  ```bash
  docker build -t support-buddy-backend ./backend
  docker run --env-file ./backend/.env -p 8000:8000 support-buddy-backend
  ```

### Notes
- The `.venv/` directory is now the standard location for the Python virtual environment (see `.gitignore`).
- All Python dependencies are managed in `pyproject.toml` and installed with `uv sync` (see [start_backend.sh](./start_backend.sh) and [backend/Dockerfile](./backend/Dockerfile)).

## Starting the Frontend

To start the frontend React application, use the provided script:
```sh
./start_frontend.sh
```

## Activating the Backend Python Virtual Environment

To activate the backend's Python virtual environment, use the provided script:
```sh
# For Linux/macOS (bash/zsh)
source ./set_venv.sh
```

For Windows (PowerShell), open PowerShell as Administrator (if needed for execution policy) and run:

```powershell
# Make sure execution policy allows running local scripts
# You might need to run: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
. .\set_venv.ps1
```

## Environment Variables
The backend requires a `.env` file with configuration for:
```env
# Jira Settings
JIRA_URL=http://localhost:9090
JIRA_USERNAME=admin
JIRA_PASSWORD=admin      # For local/server instance
JIRA_API_TOKEN=          # For cloud instance
# Confluence Settings
CONFLUENCE_USERNAME=your-confluence-username
CONFLUENCE_PASSWORD=your-confluence-password
# Vector DB Settings
VECTOR_DB_PATH=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# (No special StackOverflow credentials required for public Q&A ingestion)
```

## Backend Search Logic
- When searching for a Jira ID (e.g., `PROJ-123`), the backend will always boost the exact match to the top of the results (similarity score 1.0), regardless of embedding similarity.
- Jira ticket IDs are always included in the embedded text for accurate matching.

## Unified Search Result API
- `/search` endpoint returns a single `results` array, sorted by similarity percentage, with a `type` field for each result (`vector_issue`, `confluence`, `stackoverflow`)

### Example Response
```json
{
  "results": [
    { "type": "vector_issue", "id": "...", "similarity_score": 0.91, ... },
    { "type": "confluence", "page_id": "...", "similarity_score": 0.87, ... },
    { "type": "stackoverflow", "id": "...", "similarity_score": 0.85, ... }
  ],
  "vector_issues": [...],
  "confluence_results": [...],
  "stackoverflow_results": [...]
}
```

## Logging

Backend logs are written to `backend/app/logs/backend.log`. You can also view logs in the console.

## Running Tests

### Backend
From the `backend/` directory:
```bash
pytest --maxfail=1 --disable-warnings -v
```

### Frontend
From the `frontend/` directory:
```bash
npm test
```


## ChromaDB Setup (Docker Compose)

ChromaDB is now run as a Docker container using Docker Compose. The `docker-compose.yml` file includes a `chroma` service with a healthcheck that ensures the service is healthy only if it returns HTTP 200 on its heartbeat endpoint.

**To start all services (including ChromaDB):**
```bash
docker compose up -d
```

- The ChromaDB Admin UI is available at [http://localhost:3500](http://localhost:3500) if you wish to monitor collections.
- The backend connects to ChromaDB via HTTP (see below).

## Backend ChromaDB HTTP Client Configuration

The backend is configured to connect to ChromaDB using the HTTP API (`chroma_use_http=True`).

- Ensure your `pyproject.toml` specifies a `chromadb` version that matches the Docker image (e.g., `chromadb==1.0.5` if using `chromadb/chroma:1.0.5`).
- The backend will use `chromadb.HttpClient` when `chroma_use_http` is enabled. Do not pass local-only settings (like `persist_directory`) to the HTTP client.
- Example environment variable (in `backend/.env`):
  ```env
  CHROMA_USE_HTTP=true
  CHROMA_SERVER_HOST=chroma
  CHROMA_SERVER_HTTP_PORT=8000
  ```

- The backend will connect to ChromaDB at `http://chroma:8000` when running in Docker Compose.

## Healthcheck for ChromaDB

The `docker-compose.yml` healthcheck for ChromaDB is:
```yaml
test: ["CMD", "bash", "-c", "curl -fsS -o /dev/null -w '%{http_code}' http://localhost:8000/api/v2/heartbeat | grep 200"]
interval: 30s
timeout: 10s
retries: 3
```

This ensures the service is only marked healthy if it returns HTTP 200.

## Troubleshooting: ChromaDB HTTP Mode

If you see an error like:
```
{"error":"KeyError('_type')"}
```

when using `chroma_use_http=True`, this usually means:
- The client and server versions of ChromaDB are mismatched.
- You are using a feature or API call not supported in HTTP mode.

**How to fix:**
1. Ensure the `chromadb` Python package version in your backend matches the Docker image version.
2. Ensure you are using `chromadb.HttpClient` and not `PersistentClient`.
3. Avoid passing local-only settings (like `persist_directory`) to the HTTP client.

**To update your backend's ChromaDB version:**
```bash
uv pip install --upgrade chromadb==1.0.5
```

**If you change the Docker image version, update your backend's `chromadb` version to match.**