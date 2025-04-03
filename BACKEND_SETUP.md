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

Both scripts will create a `.env` file from `.env.example` if one doesn't exist. You should edit this file with your actual configuration values:

- Database connection details
- Jira API credentials
- Vector database path
- File upload directory
- LLM settings

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