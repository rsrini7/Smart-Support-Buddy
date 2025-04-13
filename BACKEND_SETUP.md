# Backend Setup Guide

This guide explains how to set up and run the backend for the Production Issue Identifier application.

## Available Scripts

Two scripts are provided for running the backend:

### 1. Shell Script (Bash)

```bash
./start_backend.sh
```

This script:
- Creates a virtual environment if it doesn't exist
- Installs dependencies from requirements.txt
- Sets up necessary data directories
- Creates a .env file from .env.example if needed
- Starts the FastAPI server on port 8000

### 2. Python Script (Cross-platform)

```bash
./run_backend.py
```

This script provides more flexibility with command-line options:

```
usage: run_backend.py [-h] [--host HOST] [--port PORT] [--no-reload] [--skip-deps] [--venv VENV]

Production Issue Identifier Backend Runner

options:
  -h, --help     show this help message and exit
  --host HOST    Host to bind the server to (default: 0.0.0.0)
  --port PORT    Port to bind the server to (default: 8000)
  --no-reload    Disable auto-reload on code changes
  --skip-deps    Skip dependency installation
  --venv VENV    Path to virtual environment (default: venv)
```

## Environment Setup

The backend requires several configuration parameters set through environment variables. A `.env` file will be created from `.env.example` if it doesn't exist.

### Required Configuration

1. **Database Settings**
   ```
   DATABASE_URL=postgresql://postgres:postgres@localhost/prodissue
   ```

2. **Jira Integration**
   - For Local Server:
     ```
     JIRA_URL=http://localhost:9090
     JIRA_USERNAME=admin
     JIRA_PASSWORD=admin
     ```
   - For Atlassian Cloud:
     ```
     JIRA_URL=https://company.atlassian.net
     JIRA_USERNAME=your-email
     JIRA_API_TOKEN=your-api-token
     ```

3. **Vector Database**
   ```
   VECTOR_DB_PATH=./data/vectordb
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

## Development vs Production

### Development

For development, use:

```bash
./run_backend.py
```

This will start the server with auto-reload enabled, so changes to the code will automatically restart the server.

### Production

For production, use:

```bash
./run_backend.py --no-reload --host 0.0.0.0 --port 8000
```

This disables auto-reload for better performance and stability in production environments.

## Troubleshooting

If you encounter issues:

1. Ensure Python 3.8+ is installed
2. Check that all required dependencies are available
3. Verify your `.env` file has the correct configuration
4. Make sure the necessary directories exist and are writable
5. Check the console output for specific error messages

## Monitoring & Logging

### Log Configuration
- Logs are stored in `backend/logs/`
- Configure log levels in `backend/app/core/logging_config.py`
- Component-specific logging enabled for:
  - MSG parsing
  - Jira integration
  - Vector operations
  - Search requests

### Vector Database Management
- ChromaDB Admin UI available at http://localhost:3500
- Monitor collection health and statistics
- View embedding performance metrics
- Manage vector data directly

### Health Checks
- Backend API health: http://localhost:9000/health
- Database connections auto-verified on startup
- Vector DB collections validated during initialization
- Jira connectivity tested on startup

## Performance Tuning

### Vector Search Optimization
1. **Similarity Threshold**
   - Configure in `backend/app/core/similarity_config.json`
   - Default: 0.2 (range 0-1)
   - Higher values = more precise matches
   - Lower values = more results

2. **Resource Management**
   - Regular cleanup of processed files
   - Archive old vector embeddings
   - Monitor disk space usage
   - Optimize batch sizes for ingestion

3. **Query Performance**
   - Use appropriate result limits
   - Monitor response times in logs
   - Index only relevant content
   - Configure proper batch sizes

## Security Considerations

1. **API Security**
   - CORS configuration in settings
   - Rate limiting on endpoints
   - Input validation for all requests
   - Secure file handling

2. **Integration Security**
   - Jira credential management
   - API token rotation
   - SSL verification for cloud instances
   - Secure environment variable handling