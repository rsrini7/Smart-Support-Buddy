#!/bin/bash

# Colors for output
GREEN="\033[0;32m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# Function to check if ChromaDB is healthy
check_health() {
    for i in {1..30}; do
        if curl -s http://localhost:8000/api/v2/heartbeat > /dev/null; then
            echo -e "${GREEN}ChromaDB is healthy!${NC}"
            return 0
        fi
        echo "Waiting for ChromaDB to be ready... ($i/30)"
        sleep 2
    done
    echo -e "${RED}ChromaDB failed to become healthy within timeout${NC}"
    return 1
}

# Function to start ChromaDB
start_chroma() {
    echo "Starting ChromaDB..."
    docker compose up -d chroma
    check_health
}

# Function to stop ChromaDB
stop_chroma() {
    echo "Stopping ChromaDB..."
    docker compose down
}

# Main script
case "$1" in
    start)
        start_chroma
        ;;
    stop)
        stop_chroma
        ;;
    restart)
        stop_chroma
        sleep 2
        start_chroma
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac