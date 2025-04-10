# Smart Support Buddy

A GenAI-powered solution for handling support issues / queries by analyzing Microsoft Outlook MSG files and Jira tickets to identify root causes and solutions.

## Overview

This application helps teams manage support issues / queries by:

1. Reading and parsing Microsoft Outlook MSG files containing issue details
2. Integrating with Jira to correlate tickets with issue reports
3. Storing the extracted information in a vector database for semantic search
4. Providing a simple UI to query historical issues and find relevant solutions

## Features

- MSG file parsing with metadata and attachment extraction
- Jira integration with bi-directional linking
- Semantic search using sentence transformers
- Bulk ingestion of MSG files
- Vector search with similarity scoring
- Responsive Material UI interface
- Chroma Admin UI for vector database management

## Architecture

The system consists of the following components:

- **MSG Parser**: Extracts text and metadata from Outlook MSG files
- **Jira Integration**: Connects to Jira API to fetch ticket information
- **Vector Database**: Stores embeddings of issue descriptions and solutions for semantic search
- **GenAI Engine**: Uses open-source LLM to process and analyze issue data
- **Web UI**: Simple interface for querying the system

## Tech Stack

- **Backend**: Python with FastAPI
- **Frontend**: React with Material-UI
- **Vector Store**: ChromaDB with sentence-transformers
- **Database**: PostgreSQL (for structured data)
- **MSG Parsing**: extract-msg library
- **Jira Integration**: Jira REST API client

## Setup Instructions

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt` and `npm install` in the frontend directory
3. Configure environment variables for Jira connection
4. Run the backend with `uvicorn app.main:app --reload`
5. Run the frontend with `npm start` in the frontend directory

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

# File Storage
UPLOAD_DIR=./data/uploads
```

A sample `.env.example` is created automatically during backend setup. Edit `.env` with your actual values. See **BACKEND_SETUP.md** for details.

## Usage

1. Upload MSG files through the UI or place them in the designated directory
2. Link Jira tickets to the uploaded MSG files
3. Use the semantic search to find similar issues:
   - Search by description text
   - Filter by Jira ticket ID
   - Sort by similarity score
4. View detailed issue information including:
   - Original MSG content and metadata
   - Linked Jira ticket details
   - Related issues based on similarity
5. Bulk ingest MSG files using the Tools menu

## Project Structure

```
├── backend/               # Python FastAPI backend
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core application logic
│   │   ├── db/            # Database models and connections
│   │   ├── services/      # Business logic services
│   │   └── main.py        # Application entry point
├── frontend/              # React frontend
│   ├── public/
│   └── src/
│       ├── components/    # UI components
│       ├── pages/         # Application pages
│       ├── services/      # API service connections
│       └── App.js         # Main application component
└── README.md             # Project documentation
```

## Docker Setup

You can run the entire system using Docker Compose:

```bash
docker-compose up --build
```

This will start:

- **Backend API** at [http://localhost:9000](http://localhost:9000)
- **Jira** at [http://localhost:9090](http://localhost:9090)
- **Chroma Vector DB** at [http://localhost:8000](http://localhost:8000)
- **Chroma Admin UI** at [http://localhost:4000](http://localhost:4000)
- **PostgreSQL** database for Jira

The backend container uses environment variables from `backend/.env.docker`. Jira is pre-configured via mounted files in `jira-setup-files` and `jira-config`.

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

## Jira Setup

After starting the containers with Docker Compose, Jira will be accessible at [http://localhost:9090](http://localhost:9090).

On first launch, complete the Jira setup wizard:

1. **License**: Enter your Jira license key (evaluation or purchased).
2. **Admin User**: Create the initial Jira administrator account.
3. **Database**: The database connection is pre-configured via mounted `dbconfig.xml`.
4. **Email & Base URL**: Configure as needed.
5. **Projects**: Create new projects or import existing ones.
6. **API Access**: Generate an API token or create a dedicated user for API access, and update your backend `.env` file with these credentials.

Subsequent startups will skip this wizard, as the data is persisted in the Docker volume.

## Frontend Production Build

To create an optimized production build of the frontend:

```bash
cd frontend
npm run build
```

This outputs static files to `frontend/build/` for deployment.
