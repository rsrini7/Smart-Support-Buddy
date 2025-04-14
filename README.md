# Support Buddy

A GenAI-powered solution for handling support issues / queries by analyzing Microsoft Outlook MSG files, Jira tickets, Confluence pages, and StackOverflow Q&A to identify root causes and solutions.

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
- **StackOverflow integration: ingest, index, and search StackOverflow Q&A**
- **Unified search results: All sources (Issues, Confluence, Stack Overflow) are now combined and sorted by similarity percentage in a single backend response for the frontend to display.**
- **Automatic deduplication for all sources (MSG, Jira, Confluence, StackOverflow) using content-based hashing to prevent duplicate entries in the vector database**
- Semantic search using sentence transformers
- Bulk ingestion of MSG files, Confluence pages, and StackOverflow Q&A
- Vector search with configurable similarity threshold (0-1 range, default 0.2)
- Responsive Material UI interface with dedicated configuration page for search settings
- Chroma Admin UI for vector database management and monitoring

## System Architecture

### Core Components

1. **Backend Services** (FastAPI)
   - MSG Parser: Extracts data from Outlook MSG files including metadata and attachments
   - Jira Service: Handles Jira ticket integration and synchronization
   - Confluence Service: Manages Confluence page ingestion and search
   - **StackOverflow Service: Handles ingestion, indexing, and semantic search of StackOverflow Q&A**
   - Vector Service: Manages ChromaDB operations, semantic search, and deduplication for all sources
   - **Unified Search Aggregation: Combines and sorts all results by similarity percentage before returning to the frontend. Legacy result arrays are deprecated for UI use.**

2. **Vector Database** (ChromaDB)
   - Stores embeddings for semantic search
   - Content-based deduplication for all sources (MSG, Jira, Confluence, StackOverflow) using SHA256 hashes
   - Collections for:
     - Support issues (MSG files)
     - Jira tickets
     - Confluence pages
     - **StackOverflow Q&A**
   - Configurable similarity threshold
   - Admin UI for monitoring

3. **Knowledge Integration**
   - Bi-directional Jira ticket linking
   - Confluence page ingestion and search
   - **StackOverflow Q&A ingestion, indexing, and search**
   - Automatic deduplication for all sources (MSG, Jira, Confluence, StackOverflow)
   - Unified search across all sources

4. **Frontend** (React/Material-UI)
   - Search interface with configurable parameters
   - Issue management and ingestion tools
   - Configuration management
   - Real-time search results with similarity scores

## Integrations & Technologies

### Knowledge Sources
1. **MSG Files**
   - Supports Outlook MSG format
   - Extracts: metadata, body, attachments
   - Auto-detects Jira references
   - Bulk ingestion support

2. **Jira Integration**
   - Supports both Server and Cloud instances
   - Real-time ticket synchronization
   - Bi-directional linking with issues
   - Custom field mapping support

3. **Confluence**
   - Page content extraction and indexing
   - Metadata preservation
   - Link management
   - Search by similarity

4. **StackOverflow**
   - **Q&A content ingestion via question URL**
   - **Answer scoring, ranking, and acceptance status**
   - Metadata preservation
   - Semantic similarity search

### Technology Stack
- **Backend**: Python 3.8+ with FastAPI
- **Frontend**: React 18+ with Material UI
- **Vector Store**: ChromaDB with sentence-transformers
- **Databases**: 
  - PostgreSQL: Structured data storage
  - ChromaDB: Vector embeddings
- **Core Libraries**:
  - extract-msg: MSG file parsing
  - sentence-transformers: Text embeddings
  - chromadb: Vector database
  - jira: API client

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js and npm
- Docker and Docker Compose (for containerized setup)
- Jira instance (local or cloud)
- Confluence instance (local, via Docker Compose)
- **Internet access for StackOverflow Q&A ingestion**
- PostgreSQL (or use containerized version)

### Development Setup
1. Clone this repository
2. Install backend dependencies:
   ```bash
   # Using uv (recommended)
   uv venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   uv pip install -r requirements.txt
   ```
   Or use traditional pip:
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

## Backend Startup & Orchestration

- The backend can be started using the shell script:
  ```bash
  ./start_backend.sh
  ```
- This script:
  - Starts Docker Compose services (ChromaDB, PostgreSQL, Jira, Confluence, etc.)
  - Waits for ChromaDB to be healthy
  - Waits for Jira to be ready (via REST API)
  - **Waits for Confluence to be ready** (via HTTP status endpoint)
  - Sets up the Python virtual environment and dependencies
  - Starts the FastAPI server on port **9000**
- The script will exit with an error if Jira or Confluence fail to start after multiple attempts.

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

Configuration Options:

1. Environment Variables:
   - Set in `.env` file (created from `.env.example` during setup)
   - Can override any setting at runtime
   - See **BACKEND_SETUP.md** for detailed configuration

2. Similarity Search Configuration:
   - Default threshold: 0.2 (configured in `backend/app/core/similarity_config.json`)
   - Adjustable via frontend Config page
   - Higher values (closer to 1) mean stricter matching
   - Lower values (closer to 0) return more results
   - Changes persist across server restarts

## Docker Deployment

Run the complete system using Docker Compose:

```bash
docker-compose up --build
```

Services and Ports:
- Backend API: [http://localhost:9000](http://localhost:9000)
- Jira Server: [http://localhost:9090](http://localhost:9090)
- Confluence: [http://localhost:8090](http://localhost:8090)
- ChromaDB: [http://localhost:8000](http://localhost:8000)
- Chroma Admin UI: [http://localhost:3500](http://localhost:3500)
- PostgreSQL: 
  - Jira DB: localhost:5432
  - Confluence DB: localhost:5433

Volumes:
- jira_data: Jira application data
- postgres_data: Jira database
- confluence-data: Confluence content
- confluence_postgres_data: Confluence database

## Backend Setup

For detailed backend setup instructions, including running with or without Docker, and details on the new Confluence startup wait logic, see **BACKEND_SETUP.md**.

## Project Structure

```
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core application logic and config (e.g., similarity_config.json)
│   │   ├── db/            # Database models and connections
│   │   ├── services/      # Business logic services:
│   │   │   ├── vector_service.py         # Vector DB operations
│   │   │   ├── confluence_service.py     # Confluence integration
│   │   │   ├── stackoverflow_service.py  # **StackOverflow integration**
│   │   │   ├── jira_service.py           # Jira integration
│   │   │   └── msg_parser.py             # MSG file parsing
│   │   └── main.py        # Application entry point
├── frontend/              # React frontend
│   ├── public/
│   └── src/
│       ├── components/    # UI components
│       ├── pages/         # Application pages (including ConfigPage.js for settings)
│       ├── services/      # API service connections
│       └── App.js         # Main application component
└── README.md             # Project documentation
```

## Recent Enhancements

### Unified Search Results & Similarity Sorting (2025)
- The search functionality now returns a single, unified list of results from issues, Confluence, and Stack Overflow, sorted by similarity percentage (highest first).
- The backend combines and sorts all results, so the frontend simply displays them in the order received.
- The UI now supports both a single-page result view and tabbed views, all powered by the same unified, sorted data.
- All action buttons (e.g., "View Details", "View Page", "View on Stack Overflow") are now consistently placed at the bottom of each result card.

### Navigation Improvements
- "View Details" button for issues (Jira, MSG) navigates to the Issue Details page.
- Source links (Jira, Confluence, Stack Overflow) are clearly shown for each result type.

## Testing

### Frontend

Run React tests:

```bash
cd frontend
npm test
```

### Backend

Run backend tests:

```bash
pytest backend/tests
```

## Monitoring & Maintenance

- ChromaDB Admin UI: [http://localhost:3500](http://localhost:3500)
- Backend logs: `backend/logs`
- Log levels configurable in `backend/app/core/logging_config.py`
- Component-specific logging for:
  - MSG parsing
  - Jira integration
  - Confluence integration
  - **StackOverflow integration**
  - Vector operations
  - Search requests

## Troubleshooting

- If Jira or Confluence fail to start, check Docker container logs and ensure ports 9090 (Jira) and 8090 (Confluence) are available.
- **If StackOverflow Q&A ingestion fails, check internet connectivity and ensure the question URL is valid.**
- The backend startup script will exit with an error if either service is not ready after multiple attempts.

## Performance Optimization

- Adjust similarity threshold for search quality
- Monitor vector DB size and clean up as needed
- Archive old vector embeddings
- Optimize batch ingestion sizes

## Deduplication Logic

- All ingestion endpoints (MSG, Jira, Confluence, StackOverflow) now prevent duplicate entries in the vector database.
- Deduplication is performed using a SHA256 hash of the main content fields (e.g., subject+body for MSG, summary+description+ID for Jira, content for Confluence, question/answer text for StackOverflow).
- Before insertion, the system checks for an existing entry with the same hash and skips insertion if a duplicate is found.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Data Flow & Processing](#data-flow--processing)
- [Setup Instructions](#setup-instructions)
- [Backend Startup & Orchestration](#backend-startup--orchestration)
- [Unified Search Result API](#unified-search-result-api)
- [Monitoring & Logging](#monitoring--logging)
- [Performance Tuning](#performance-tuning)
- [Security Considerations](#security-considerations)
- [System Operations](#system-operations)
- [Summary](#summary)

## Overview
Support Buddy helps teams manage support issues and queries by:
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

### Architecture Diagram
```
User --> Web UI (React) --> Backend API (FastAPI)
Backend --> MSG Parser, Jira, Confluence, StackOverflow, Vector DB (ChromaDB), PostgreSQL
```

## Data Flow & Processing
### 1. Data Ingestion
- MSG Files: UI upload or bulk import; metadata and attachment extraction; automatic Jira reference detection
- Confluence: Page import via URL
- StackOverflow: Q&A ingestion via question URL
- Jira: Ticket synchronization

### 2. Processing Pipeline
- Text extraction, cleaning, and embedding
- Metadata organization and collection
- Content-based deduplication

### 3. Search & Retrieval
- Query embedding and multi-source search
- Unified result aggregation and similarity sorting
- Source-specific formatting and navigation

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

## Backend Startup & Orchestration
- Start backend with `./start_backend.sh` (starts Docker Compose services, waits for ChromaDB, Jira, and Confluence)
- Virtual environment and dependencies setup
- FastAPI server runs on port 9000
- Script exits if Jira or Confluence fail to start

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

- Set in `.env` file (created from `.env.example` during setup)
- Similarity threshold configurable in `backend/app/core/similarity_config.json` (default: 0.2)
- Adjustable via frontend Config page

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
