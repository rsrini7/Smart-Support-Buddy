#!/bin/bash

# This script configures and starts the frontend

cd "$(dirname "$0")/frontend" || exit 1

# Install dependencies if node_modules does not exist
if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

echo "Starting frontend..."
npm start
