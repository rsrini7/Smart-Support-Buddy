#!/bin/bash

# Support Buddy - Backend Startup Script
# This script starts Docker services and the FastAPI backend server

set -e  # Exit immediately if a command exits with a non-zero status

echo "===== Support Buddy Backend Setup ====="

# Define directories
BACKEND_DIR="$(pwd)/backend"
DATA_DIR="$BACKEND_DIR/data"
VECTOR_DB_DIR="$DATA_DIR/chroma"

# Start Docker Compose services
echo "Starting Docker Compose services..."
docker compose up -d chroma postgres jira confluence-postgres confluence

# Wait for ChromaDB to be healthy
echo "Waiting for ChromaDB to be healthy..."
until curl -s -f "http://localhost:8000/api/v2/heartbeat" > /dev/null 2>&1; do
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

# Wait for Confluence to be ready (similar to Jira)
echo "Waiting for Confluence to be ready..."
sleep 10  # Initial wait time before checking Confluence
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    RESPONSE=$(curl -s "http://localhost:8090/status")
    STATE=$(echo "$RESPONSE" | grep -o '"state":"[^\"]*"' | cut -d':' -f2 | tr -d '"')
    if [ "$STATE" = "RUNNING" ]; then
        echo "Confluence is ready and running!"
        break
    elif [ "$STATE" = "FAILED" ] || [ "$STATE" = "ERROR" ]; then
        echo "Confluence state is $STATE. Restarting confluence container..."
        docker compose restart confluence
        echo "Waiting 15 seconds for Confluence to restart..."
        sleep 15
    else
        echo "Confluence is still starting up or in unknown state: $STATE"
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "Retrying in 10 seconds... (Attempt $RETRY_COUNT/$MAX_RETRIES)"
        sleep 10
    fi
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "Error: Confluence failed to reach RUNNING state after $MAX_RETRIES attempts"
    echo "Please check:
    1. Docker containers are running (docker ps)
    2. Confluence is running on port 8090"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Check if 'uv' command exists, if not, install it using the provided script
if ! command -v uv &> /dev/null; then
    echo "'uv' command not found. Installing 'uv'..."
    # Install 'uv' for Linux or macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Add $HOME/.local/bin to PATH if not already present
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies (in backend dir)
echo "Installing dependencies..."
uv sync

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Create necessary directories
echo "Setting up data directories..."
mkdir -p "$VECTOR_DB_DIR"

# Check for .env file and create from example if it doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env file from example..."
    cp ".env.example" ".env"
    echo "WARNING: A default .env file has been created. Please edit it with your actual configuration."
fi

# Start the FastAPI server
echo "Starting FastAPI server..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 9000 --reload

echo "Server stopped."