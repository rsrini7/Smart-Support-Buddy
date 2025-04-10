# Production Issue Identifier

A GenAI-powered solution for handling support issues / queries by analyzing Microsoft Outlook MSG files and Jira tickets to identify root causes and solutions.

## Overview

This application helps teams manage support issues / queries by:

1. Reading and parsing Microsoft Outlook MSG files containing issue details
2. Integrating with Jira to correlate tickets with issue reports
3. Storing the extracted information in a vector database for semantic search
4. Providing a simple UI to query historical issues and find relevant solutions

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
- **Database**: PostgreSQL (for structured data) + Chroma/Qdrant (for vector embeddings)
- **AI Components**: LangChain or LlamaIndex with an open-source LLM
- **MSG Parsing**: extract-msg library
- **Jira Integration**: Jira REST API client

## Setup Instructions

1. Clone this repository
2. Install dependencies with `pip install -r requirements.txt` and `npm install` in the frontend directory
3. Configure environment variables for Jira connection
4. Run the backend with `uvicorn app.main:app --reload`
5. Run the frontend with `npm start` in the frontend directory

## Usage

1. Upload MSG files through the UI or place them in the designated directory
2. Link Jira tickets to the uploaded MSG files
3. Query the system when similar support issues / queries occur to find historical solutions

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