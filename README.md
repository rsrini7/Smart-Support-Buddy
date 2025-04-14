# Support Buddy

A GenAI-powered solution for handling support issues / queries by analyzing Microsoft Outlook MSG files, Jira tickets, Confluence pages, and StackOverflow Q&A to identify root causes and solutions.

## Project Structure

```
prodissue-identifier/
├── .git/
├── .gitignore
├── LICENSE
├── README.md                # ← Single, up-to-date documentation source
├── UV_MIGRATION.md
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── Dockerfile
│   ├── LearnChromaDB.py
│   ├── app/
│   │   ├── __init__.py
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── main.py
│   │   ├── services/
│   │   └── utils/
│   ├── data/
│   ├── pytest.ini
│   └── tests/
├── check_chromadb.py
├── chroma.sh
├── confluence-config/
├── confluence-setup-files/
├── data/
├── deduplication_plan.md
├── docker-compose.yml
├── frontend/
│   ├── .env
│   ├── node_modules/
│   ├── package-lock.json
│   ├── package.json
│   ├── public/
│   └── src/
├── jira-config/
├── jira-setup-files/
├── requirements.txt
├── run_backend.py
├── start_backend.sh
└── venv/
```

## Overview

This application helps teams manage support issues / queries by:

1. Reading and parsing Microsoft Outlook MSG files containing issue details
2. Integrating with Jira to correlate tickets with issue reports
3. Ingesting and searching knowledge from Confluence pages and StackOverflow Q&A
4. Storing the extracted information in a vector database for semantic search
5. Providing a simple UI to query historical issues and find relevant solutions, and to configure search parameters

## Features

- MSG file parsing with metadata and attachment extraction
- Jira integration with bi-directional linking
- Confluence integration: ingest and search Confluence pages
- StackOverflow integration: ingest, index, and search StackOverflow Q&A
- Unified search results: All sources (Issues, Confluence, Stack Overflow) are combined and sorted by similarity percentage in a single backend response for the frontend to display
- Automatic deduplication for all sources using content-based hashing
- Semantic search with sentence transformers
- Bulk ingestion of MSG files, Confluence pages, and StackOverflow Q&A
- Vector search with configurable similarity threshold
- Responsive Material UI interface and configuration management
- Chroma Admin UI for vector database management

## System Architecture

### Core Components

1. **Backend Services** (FastAPI)
   - MSG Parser: Extracts data from Outlook MSG files
   - Jira Service: Handles Jira ticket integration
   - Confluence Service: Manages Confluence page ingestion and search
   - StackOverflow Service: Handles ingestion, indexing, and semantic search of StackOverflow Q&A
   - Vector Service: Manages ChromaDB operations, semantic search, and deduplication
   - Unified Search Aggregation: Combines and sorts all results by similarity percentage before returning to the frontend. Legacy result arrays are deprecated for UI use.

2. **Vector Database** (ChromaDB)
   - Stores embeddings for semantic search
   - Content-based deduplication using SHA256 hashes
   - Collections for support issues, Jira tickets, Confluence pages, StackOverflow Q&A
   - Configurable similarity threshold
   - Admin UI for monitoring

3. **Knowledge Integration**
   - Bi-directional Jira ticket linking
   - Confluence page ingestion and search
   - StackOverflow Q&A ingestion, indexing, and search
   - Unified search across all sources

4. **Frontend** (React/Material-UI)
   - Search interface with configurable parameters
   - Issue management and ingestion tools
   - Real-time search results with similarity scores
   - Unified results rendering: All search views use the unified, similarity-sorted results array

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js and npm
- Docker and Docker Compose (for containerized setup)
- Jira instance (local or cloud)
- Confluence instance (local, via Docker Compose)
- Internet access for StackOverflow Q&A ingestion
- PostgreSQL (or use containerized version)

### Development Setup
1. Clone this repository
2. Install backend dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Configure environment variables (see Environment Variables section)
5. Start the services:
   - Development mode:
     ```bash
     ./run_backend.py  # Starts backend with auto-reload
     cd frontend && npm start  # Starts frontend dev server
     ```
   - Production mode:
     ```bash
     ./run_backend.py --no-reload --host 0.0.0.0
     cd frontend && npm run build
     ```

## Environment Variables
The backend requires a `.env` file with configuration for:
```bash
# Database Settings
DATABASE_URL=postgresql://postgres:postgres@localhost/prodissue
# Jira Settings
JIRA_URL=http://localhost:9090
JIRA_USERNAME=admin
JIRA_PASSWORD=admin      # For local instance
JIRA_API_TOKEN=          # For cloud instance
# Vector DB Settings
VECTOR_DB_PATH=./data/vectordb
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# (No special StackOverflow credentials required for public Q&A ingestion)
```

## Backend Startup & Orchestration
- Start backend with `./start_backend.sh` (starts Docker Compose services, waits for ChromaDB, Jira, and Confluence)
- Virtual environment and dependencies setup
- FastAPI server runs on port 9000
- Script exits if Jira or Confluence fail to start

## Unified Search Result API
- `/search` endpoint returns a single `results` array, sorted by similarity percentage, with a `type` field for each result (`jira`, `msg`, `confluence`, `stackoverflow`)
- Legacy arrays (`vector_issues`, `confluence_results`, `stackoverflow_results`) are deprecated and retained only for backward compatibility
- **Frontend and all new integrations must use the unified `results` array**

### Example Response
```json
{
  "results": [
    { "type": "jira", "id": "...", "similarity_score": 0.91, ... },
    { "type": "confluence", "id": "...", "similarity_score": 0.87, ... },
    { "type": "stackoverflow", "id": "...", "similarity_score": 0.85, ... }
  ],
  "vector_issues": [...],
  "confluence_results": [...],
  "stackoverflow_results": [...]
}
```

## Monitoring & Logging
- Logs stored in `backend/logs/`
- Configure log levels in `backend/app/core/logging_config.py`
- Component-specific logging for MSG parsing, Jira, Confluence, StackOverflow, deduplication, vector ops, and search
- ChromaDB Admin UI at http://localhost:3500 for vector DB management
- Health checks: backend API `/health`, DB connections, vector DB collections, Jira/Confluence connectivity, StackOverflow ingestion

## Performance Tuning
- Similarity threshold (default 0.2) in `backend/app/core/similarity_config.json`
- Resource management: cleanup, archiving, disk space monitoring
- Query performance: result limits, response times, batch sizes

## Security Considerations
- API security: CORS, rate limiting, input validation, secure file handling
- Integration security: Jira/Confluence credentials, API token rotation
- Data protection: secure file handling, DB encryption, network isolation, access controls

## System Operations
### Deployment
- Development: `./run_backend.py`, `npm start`
- Production: Docker Compose, persistent data volumes
- Backend startup script ensures all services are ready before launch

### Monitoring
- Service health: API endpoints, DB checks, vector DB status, Jira/Confluence connectivity
- Performance metrics: query times, embedding speed, storage, cache

### Testing & Quality
- Automated tests: backend (pytest), frontend (React), integration, vector search validation
- Performance testing: load, batch, response times, memory

### Configuration Management
- `.env` for service settings
- Docker Compose for orchestration
- Jira/Confluence/StackOverflow setup
- Vector DB and file storage configuration

### Security
- Authentication: Jira/Confluence credentials, StackOverflow public Q&A does not require authentication
- Data protection: file handling, encryption, network, access controls

## Summary
Support Buddy provides a comprehensive solution for support issue management through:
1. **Knowledge Integration**: MSG file parsing, Jira synchronization, Confluence integration, StackOverflow Q&A ingestion, automatic deduplication
2. **Intelligent Search**: Vector-based semantic search, configurable similarity, cross-source aggregation, real-time ranking
3. **Modern Architecture**: Containerized microservices, vector database, React UI, extensible API design
