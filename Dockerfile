FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Optional: download small spaCy model at build time (best-effort)
RUN python -m spacy download en_core_web_sm || true

# Expose the port the app runs on
EXPOSE 8000

# Use Uvicorn with multiple workers for better concurrency
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
