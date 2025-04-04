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

# Wait for Jira to be ready (this may take a few minutes)
echo "Waiting for Jira to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s -f "http://localhost:9090/rest/api/2/serverInfo" > /dev/null 2>&1; then
        echo "Jira is ready!"
        break
    fi
    echo "Waiting for Jira... (Attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 10
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Jira failed to start after $MAX_RETRIES attempts"
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