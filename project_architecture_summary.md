# Support Buddy – Comprehensive Project Overview

## Purpose
A GenAI-powered solution for handling support issues/queries by analyzing Microsoft Outlook MSG files, Jira tickets, Confluence pages, and StackOverflow Q&A to identify root causes and solutions.

---

## Architecture Overview

```mermaid
flowchart TD
    A[User] --> B[Web UI (React)]
    B --> C[Backend API (FastAPI)]
    C --> D[MSG Parser]
    C --> E[Jira Integration]
    C --> H[Confluence Integration]
    C --> I[StackOverflow Integration]
    C --> F[Vector DB (ChromaDB)]
    C --> G[PostgreSQL]
    D --> F
    E --> G
    H --> G
    I --> F
    F --> B
    E --> B
    H --> B
    I --> B
```

---

## Components

### 1. Backend (Python/FastAPI)
- **API Endpoints**: For uploading MSG files, searching issues, linking Jira tickets, ingesting Confluence pages, and importing StackOverflow Q&A.
- **Services**:
  - `msg_parser.py`: Parses MSG files, extracts metadata and attachments.
  - `jira_service.py`: Connects to Jira API, fetches ticket info.
  - `confluence_service.py`: Handles Confluence page ingestion and search.
  - `stackoverflow_service.py`: Handles StackOverflow Q&A ingestion, indexing, and semantic search.
  - `vector_service.py`: Handles vector DB operations, semantic search, and embeddings.
- **Database**:
  - SQLAlchemy models for issues, Jira tickets, and vector embeddings.
  - Uses PostgreSQL for structured data and ChromaDB for vector storage.

### 2. Frontend (React/Material-UI)
- **Pages**:
  - Home, Upload, Ingest MSG Files, Ingest Confluence Pages, Ingest StackOverflow Q&A, Search, Issue Details.
- **Components**:
  - Header, Footer, and shared UI elements.
- **Functionality**:
  - Upload MSG files, link Jira tickets, ingest Confluence pages, import StackOverflow Q&A, perform semantic search, view and manage issues.

### 3. Jira Integration
- **Jira Server**: Runs in Docker, configured via setup files.
- **Integration**: Backend communicates with Jira via REST API for ticket info and linking.

### 4. Confluence Integration
- **Confluence Server**: Runs in Docker, configured via setup files.
- **Integration**: Backend communicates with Confluence for page ingestion and search.

### 5. StackOverflow Integration
- **StackOverflow Q&A**: Ingested via question URL, indexed, and made available for semantic search.
- **Integration**: Backend fetches Q&A content, scores and ranks answers, and stores them in the vector database for unified search.

### 6. Vector Database (ChromaDB)
- **Collections**:
  - `production_issues`: MSG files and Jira tickets
  - `confluence_pages`: Confluence content
  - `stackoverflow_qa`: Stack Overflow Q&A
- **Features**:
  - Semantic search with configurable similarity
  - Real-time embedding and indexing
  - **Automatic deduplication for all sources (MSG, Jira, Confluence, StackOverflow) using content-based SHA256 hashes**
  - Admin UI for monitoring and management
  - Persistent storage and backup support

### 7. Knowledge Integration
- **Jira**:
  - Local server or Atlassian Cloud support
  - Bi-directional ticket linking
  - Custom field mapping
  - Real-time synchronization
- **Confluence**:
  - Page content extraction and indexing
  - Metadata preservation
  - Link management
- **StackOverflow**:
  - Q&A content ingestion via URL
  - Answer scoring, ranking, and acceptance tracking
  - Semantic similarity search

### 8. Orchestration (Docker Compose & Startup Script)
- **Services**:
  - Backend API (FastAPI, port 9000)
  - ChromaDB (Vector Store)
  - ChromaDB Admin UI
  - Jira Server
  - Confluence Server
  - PostgreSQL (Jira + Confluence)
- **Startup Sequence**:
  - The backend startup script (`start_backend.sh`) starts all services via Docker Compose.
  - The script waits for ChromaDB to be healthy.
  - The script waits for Jira to be ready (via REST API).
  - **The script waits for Confluence to be ready (via HTTP status endpoint).**
  - Only after both Jira and Confluence are ready does the FastAPI server start.
  - **StackOverflow Q&A ingestion is available on demand via API endpoints.**
- **Networking**:
  - Shared Docker network
  - Exposed ports for services
  - Internal service discovery
- **Persistence**:
  - Jira data volume
  - Confluence data volume
  - PostgreSQL data volumes
  - Vector DB storage
  - Uploaded files storage

---

## Data Flow & Processing

### 1. Data Ingestion
- **MSG Files**:
  - UI upload or bulk directory import
  - Metadata and attachment extraction
  - Automatic Jira reference detection
  
- **External Knowledge**:
  - Confluence page import via URL
  - **StackOverflow Q&A ingestion via question URL**
  - Jira ticket synchronization

### 2. Processing Pipeline
- **Text Processing**:
  - Content extraction and cleaning
  - Metadata organization
  - File attachment handling
  
- **Vector Embedding**:
  - Text embedding generation
  - Metadata enhancement
  - Collection organization

### 3. Search & Retrieval
- **Query Processing**:
  - Text query embedding
  - Jira ticket lookup
  - Multi-source search (MSG, Jira, Confluence, StackOverflow)
  
- **Result Aggregation**:
  - Similarity score calculation
  - Result ranking and filtering
  - Source-specific formatting

---

## System Operations

### 1. Deployment
- **Development**:
  ```
  Backend: ./run_backend.py
  Frontend: npm start
  Vector DB: Auto-managed
  ```
  
- **Production**:
  ```
  Docker Compose: Full stack deployment
  Individual Services: Configurable ports
  Data Persistence: Docker volumes
  ```
- **Backend Startup**:
  - Use `./start_backend.sh` to orchestrate all services and ensure both Jira and Confluence are ready before backend launch.
  - **StackOverflow Q&A ingestion is available after backend startup and requires internet access.**

### 2. Monitoring
- **Service Health**:
  - API endpoint monitoring
  - Database connection checks
  - Vector DB collection status
  - Jira and Confluence integration connectivity (checked at startup)
  - **StackOverflow Q&A ingestion monitored via logs and API responses**
- **Performance Metrics**:
  - Query response times
  - Embedding generation speed
  - Storage utilization
  - Cache hit rates

### 3. Testing & Quality
- **Automated Tests**:
  - Backend: pytest coverage
  - Frontend: React testing
  - Integration tests
  - Vector search validation

- **Performance Testing**:
  - Load testing
  - Batch processing limits
  - Search response times
  - Memory utilization

---

## System Management

### 1. Configuration Management
- **Environment Configuration**:
  - `.env` file for service settings
  - Docker Compose for service orchestration
  - Configurable ports and endpoints
  - Development vs. production modes

- **Integration Setup**:
  - Jira: Local server (port 9090) or Cloud
  - Confluence: Local server (port 8090) or Cloud
  - **StackOverflow: No credentials required for public Q&A ingestion**
  - Vector DB: Persistent storage paths
  - File storage locations

### 2. Monitoring & Maintenance
- **Health Monitoring**:
  - Service status endpoints
  - Log aggregation
  - Performance metrics
  - Resource utilization
  - **Jira and Confluence readiness checked at backend startup**
  - **StackOverflow Q&A ingestion monitored via logs**

- **Data Management**:
  - Vector DB backup
  - PostgreSQL maintenance
  - File cleanup routines
  - Cache management

### 3. Security
- **Authentication**:
  - Jira API tokens/credentials
  - Confluence credentials (if required)
  - **StackOverflow: Public Q&A ingestion does not require authentication**
  - Service-to-service auth
  - Environment security

- **Data Protection**:
  - Secure file handling
  - Database encryption
  - Network isolation
  - Access controls

---

## Summary

Support Buddy provides a comprehensive solution for support issue management through:

1. **Knowledge Integration**
   - MSG file parsing and analysis
   - Jira ticket synchronization
   - Confluence knowledge base integration
   - **StackOverflow Q&A ingestion, indexing, and semantic search**
   - **Automatic deduplication for all sources (MSG, Jira, Confluence, StackOverflow) using content-based hashing**

2. **Intelligent Search**
   - Vector-based semantic search
   - Configurable similarity matching
   - Cross-source result aggregation
   - Real-time result ranking

3. **Modern Architecture**
   - Containerized microservices
   - Vector database for embeddings
   - React-based UI
   - Extensible API design

The system is designed for scalability, maintainability, and easy extension with additional knowledge sources or capabilities.