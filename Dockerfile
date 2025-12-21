# Agent Vault container
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (psycopg2 and friends)
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source
COPY packages ./packages
COPY docs ./docs

# Python deps (lean set for API)
RUN pip install --no-cache-dir fastapi uvicorn click pydantic pydantic-settings aiohttp sqlalchemy psycopg2-binary

EXPOSE 8000

CMD ["python", "packages/core/src/api.py"]
