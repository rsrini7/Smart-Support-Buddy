FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and optional lock file
COPY pyproject.toml .
# If you have a uv.lock, uncomment the next line
# COPY uv.lock .

# Install uv
RUN pip install --no-cache-dir uv

# Create and sync virtual environment
RUN uv sync && ./.venv/bin/activate

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]