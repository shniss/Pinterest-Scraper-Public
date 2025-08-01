# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set timezone to avoid apt-get update issues
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy Poetry configuration files
COPY backend/pyproject.toml backend/poetry.lock ./

# Configure Poetry to not create virtual environment (use system Python)
RUN poetry config virtualenvs.create false

# Install dependencies (only main dependencies, no dev dependencies, no root project)
RUN poetry install --only=main --no-interaction --no-ansi --no-root

# Install SpaCy model for NLP processing
RUN python -m spacy download en_core_web_sm

# Copy backend source code
COPY backend/app ./app

# Copy deployment scripts
COPY deployment ./deployment

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"] 