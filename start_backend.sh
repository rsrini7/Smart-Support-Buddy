#!/bin/bash

# Production Issue Identifier - Backend Startup Script
# This script starts Docker services and the FastAPI backend server

set -e  # Exit immediately if a command exits with a non-zero status

echo "===== Production Issue Identifier Backend Setup ====="

# Define directories
BACKEND_DIR="$(pwd)/backend"
DATA_DIR="$BACKEND_DIR/data"
UPLOAD_DIR="$DATA_DIR/uploads"
VECTOR_DB_DIR="$DATA_DIR/vectordb"

# Start Docker Compose services
echo "Starting Docker Compose services..."
docker compose up -d chroma postgres jira

# Wait for ChromaDB to be healthy
echo "Waiting for ChromaDB to be healthy..."
until curl -s -f "http://localhost:8000/api/v1/heartbeat" > /dev/null 2>&1; do
    echo "Waiting for ChromaDB..."
    sleep 5
done

# Load environment variables if .env exists
if [ -f "$BACKEND_DIR/.env" ]; then
    source "$BACKEND_DIR/.env"
fi

# Set default values for Jira credentials if not provided
JIRA_USER=${JIRA_USER:-"admin"}
JIRA_PASS=${JIRA_PASS:-"admin"}

# Wait for Jira to be ready (this may take a few minutes)
echo "Waiting for Jira to be ready..."
sleep 10  # Initial wait time before checking Jira
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Use basic auth and handle different response scenarios
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -u "$JIRA_USER:$JIRA_PASS" \
        "http://localhost:9090/rest/api/2/serverInfo")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    case "$HTTP_CODE" in
        200)
            if [ ! -z "$BODY" ]; then
                echo "Jira is ready and authenticated!"
                break
            else
                echo "Warning: Empty response from Jira server"
            fi
            ;;
        401|403)
            echo "Error: Authentication failed. Please check JIRA_USER and JIRA_PASS environment variables"
            ;;
        404)
            echo "Error: Jira API endpoint not found. Please check if Jira is properly installed"
            ;;
        503)
            echo "Jira is still starting up..."
            ;;
        *)
            echo "Unexpected response (HTTP $HTTP_CODE)"
            if [ ! -z "$BODY" ]; then
                echo "Response: $BODY"
            fi
            ;;
    esac
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "Retrying in 10 seconds... (Attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Jira failed to start after $MAX_RETRIES attempts"
    echo "Please check:
    1. Docker containers are running (docker ps)
    2. Jira credentials are correct
    3. Jira is running on port 9090"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    uv venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Create necessary directories
echo "Setting up data directories..."
mkdir -p "$UPLOAD_DIR"
mkdir -p "$VECTOR_DB_DIR"

# Check for .env file and create from example if it doesn't exist
if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
    echo "Creating .env file from example..."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    echo "WARNING: A default .env file has been created. Please edit it with your actual configuration."
fi

# Start the FastAPI server
echo "Starting FastAPI server..."
cd "$BACKEND_DIR"
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

echo "Server stopped."