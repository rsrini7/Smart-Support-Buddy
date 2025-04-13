# Support Buddy

A GenAI-powered solution for handling support issues / queries by analyzing Microsoft Outlook MSG files and Jira tickets to identify root causes and solutions.

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
- StackOverflow integration: ingest and search StackOverflow Q&A
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
   - StackOverflow Service: Handles Q&A ingestion and search
   - Vector Service: Manages ChromaDB operations and semantic search

2. **Vector Database** (ChromaDB)
   - Stores embeddings for semantic search
   - Collections for:
     - Support issues (MSG files)
     - Jira tickets
     - Confluence pages
     - StackOverflow Q&A
   - Configurable similarity threshold
   - Admin UI for monitoring

3. **Knowledge Integration**
   - Bi-directional Jira ticket linking
   - Confluence page ingestion and search
   - StackOverflow Q&A integration
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
   - Q&A content ingestion
   - Answer scoring and ranking
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

## Usage Guide

### Data Ingestion
1. **MSG Files**
   - Upload via UI: Single file upload with preview
   - Auto-extraction of: metadata, body, attachments, Jira references

2. **Knowledge Sources**
   - Confluence: Ingest pages via URL
   - StackOverflow: Import Q&A via question URL
   - Jira: Link tickets by ID or auto-detection

### Unified Search
1. **Search Methods**
   - Text-based semantic search
   - Jira ticket ID lookup
   - Combined search across all sources

2. **Result Types**
   - Support Issues (MSG + Jira)
     - Content: Original message, metadata, attachments
     - Jira: Ticket details, status, comments
     - Similarity: Vector-based matching score
   
   - Confluence Results
     - Title and content
     - URL and metadata
     - Similarity score
   
   - StackOverflow Results
     - Question title and body
     - Answers with acceptance status
     - Score and similarity ranking

3. **Configuration**
   - Adjust similarity threshold (0-1)
   - Filter by source type
   - Sort by relevance or date
   - Configure result limits per source

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
│   │   │   ├── stackoverflow_service.py  # StackOverflow integration
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

## Vector Search Configuration

### ChromaDB Setup
- **Persistent Storage**: Data stored in `./data/vectordb`
- **Collections**:
  - `production_issues`: MSG files and Jira tickets
  - `confluence_pages`: Confluence content
  - `stackoverflow_qa`: Stack Overflow Q&A
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2
- **Similarity Threshold**: 
  - Configurable via UI or config file
  - Range: 0.0-1.0 (default: 0.2)
  - Higher values = stricter matching

### Docker Deployment

Run the complete system using Docker Compose:

```bash
docker-compose up --build
```

Services and Ports:
- Backend API: [http://localhost:9000](http://localhost:9000)
- Jira Server: [http://localhost:9090](http://localhost:9090)
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

For detailed backend setup instructions, including running with or without Docker, see **BACKEND_SETUP.md**.

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

## Jira Integration Setup

The system supports both local Jira Server and Atlassian Cloud instances:

### Local Jira Server
- Accessible at [http://localhost:9090](http://localhost:9090) when using Docker Compose
- Uses basic authentication (username/password)
- Pre-configured database connection via mounted `dbconfig.xml`
- Initial setup steps:
  1. Enter Jira license key (evaluation or purchased)
  2. Create administrator account
  3. Configure email and base URL
  4. Create or import projects

### Atlassian Cloud
- Requires Jira Cloud instance URL (e.g., company.atlassian.net)
- Uses API token authentication
- Generate API token from Atlassian account settings

### Configuration
Update `.env` file with appropriate credentials:
- For local server: Set `JIRA_USERNAME` and `JIRA_PASSWORD`
- For cloud: Set `JIRA_USERNAME` and `JIRA_API_TOKEN`
- Set `JIRA_URL` to your instance URL

Subsequent startups will skip this wizard, as the data is persisted in the Docker volume.

## Frontend Production Build

To create an optimized production build of the frontend:

```bash
cd frontend
npm run build
```

This outputs static files to `frontend/build/` for deployment.

## Monitoring & Maintenance

### Vector Database
- Access ChromaDB Admin UI at http://localhost:3500 to:
  - Monitor collection sizes and health
  - View embedding statistics
  - Check search performance
  - Manage vector data

### System Health
1. **Backend Logs**
   - Check `backend/logs` for detailed logs
   - Log levels configurable in `backend/app/core/logging_config.py`
   - Component-specific logging for:
     - MSG parsing
     - Jira integration
     - Vector operations
     - Search requests

2. **Database Maintenance**
   - PostgreSQL backup recommended for production
   - Vector DB persistence in `data/vectordb`

### Troubleshooting

1. **Vector Search Issues**
   - Verify similarity threshold configuration
   - Check ChromaDB collection consistency
   - Validate embedding model availability
   - Review search query logs

2. **Integration Problems**
   - Jira: Check credentials and network access
   - Confluence: Verify page permissions
   - StackOverflow: Check API rate limits
   - MSG Files: Validate file format and encoding

3. **Common Solutions**
   - Clear browser cache for UI issues
   - Restart backend for embedding model issues
   - Check disk space for vector storage
   - Verify network connectivity for integrations

## Performance Optimization

1. **Search Performance**
   - Adjust similarity threshold based on result quality
   - Configure appropriate result limits
   - Monitor query response times
   - Index only relevant content

2. **Resource Usage**
   - Monitor vector DB size growth
   - Clean up processed MSG files
   - Archive old vector embeddings
   - Optimize batch ingestion sizes
