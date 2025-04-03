#!/bin/bash

# Production Issue Identifier - Backend Startup Script
# This script installs dependencies and starts the FastAPI backend server

set -e  # Exit immediately if a command exits with a non-zero status

echo "===== Production Issue Identifier Backend Setup ====="

# Define directories
BACKEND_DIR="$(pwd)/backend"
DATA_DIR="$BACKEND_DIR/data"
UPLOAD_DIR="$DATA_DIR/uploads"
VECTOR_DB_DIR="$DATA_DIR/vectordb"

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
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo "Server stopped."