# Support Buddy – Comprehensive Project Overview

## Purpose
A GenAI-powered solution for handling support issues/queries by analyzing Microsoft Outlook MSG files and Jira tickets to identify root causes and solutions.

---

## Architecture Overview

```mermaid
flowchart TD
    A[User] --> B[Web UI (React)]
    B --> C[Backend API (FastAPI)]
    C --> D[MSG Parser]
    C --> E[Jira Integration]
    C --> F[Vector DB (ChromaDB)]
    C --> G[PostgreSQL]
    D --> F
    E --> G
    F --> B
    E --> B
```

---

## Components

### 1. Backend (Python/FastAPI)
- **API Endpoints**: For uploading MSG files, searching issues, linking Jira tickets, and managing issues.
- **Services**:
  - `msg_parser.py`: Parses MSG files, extracts metadata and attachments.
  - `jira_service.py`: Connects to Jira API, fetches ticket info.
  - `vector_service.py`: Handles vector DB operations, semantic search, and embeddings.
- **Database**:
  - SQLAlchemy models for issues, Jira tickets, and vector embeddings.
  - Uses PostgreSQL for structured data and ChromaDB for vector storage.

### 2. Frontend (React/Material-UI)
- **Pages**:
  - Home, Upload, Ingest MSG Files, Search, Issue Details.
- **Components**:
  - Header, Footer, and shared UI elements.
- **Functionality**:
  - Upload MSG files, link Jira tickets, perform semantic search, view and manage issues.

### 3. Jira Integration
- **Jira Server**: Runs in Docker, configured via setup files.
- **Integration**: Backend communicates with Jira via REST API for ticket info and linking.

### 4. Vector Database (ChromaDB)
- **Collections**:
  - `production_issues`: MSG files and Jira tickets
  - `confluence_pages`: Confluence content
  - `stackoverflow_qa`: Stack Overflow Q&A
- **Features**:
  - Semantic search with configurable similarity
  - Real-time embedding and indexing
  - Admin UI for monitoring and management
  - Persistent storage and backup support

### 5. Knowledge Integration
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
  - Q&A content ingestion
  - Answer scoring and acceptance tracking
  - URL-based import

### 6. Orchestration (Docker Compose)
- **Services**:
  - Backend API (FastAPI)
  - ChromaDB (Vector Store)
  - ChromaDB Admin UI
  - Jira Server
  - PostgreSQL (Jira + Confluence)
- **Networking**:
  - Shared Docker network
  - Exposed ports for services
  - Internal service discovery
- **Persistence**:
  - Jira data volume
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
  - StackOverflow Q&A ingestion
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
  - Multi-source search
  
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

### 2. Monitoring
- **Service Health**:
  - API endpoint monitoring
  - Database connection checks
  - Vector DB collection status
  - Integration connectivity

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
  - Confluence: Configurable instance
  - Vector DB: Persistent storage paths
  - File storage locations

### 2. Monitoring & Maintenance
- **Health Monitoring**:
  - Service status endpoints
  - Log aggregation
  - Performance metrics
  - Resource utilization

- **Data Management**:
  - Vector DB backup
  - PostgreSQL maintenance
  - File cleanup routines
  - Cache management

### 3. Security
- **Authentication**:
  - Jira API tokens/credentials
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
   - StackOverflow Q&A incorporation

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