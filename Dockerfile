# ArcticCodex FastAPI Backend
FROM python:3.11-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Copy source code
COPY packages ./packages
COPY seed.py .

# Create vault directory
RUN mkdir -p vault

# Health check script
RUN echo '#!/bin/sh\n\
curl -f http://localhost:8000/health || exit 1\n\
' > /healthcheck.sh && chmod +x /healthcheck.sh

EXPOSE 8000

# Startup script to validate Supabase and initialize DB
RUN echo '#!/bin/bash\n\
set -e\n\
echo "Validating environment..."\n\
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then\n\
  echo "ERROR: SUPABASE_URL and SUPABASE_KEY must be set"\n\
  exit 1\n\
fi\n\
\n\
echo "Starting ArcticCodex Backend..."\n\
exec uvicorn packages.core.src.app:app --host 0.0.0.0 --port 8000\n\
' > /startup.sh && chmod +x /startup.sh

HEALTHCHECK --interval=10s --timeout=5s --retries=3 --start-period=10s \
    CMD /healthcheck.sh

ENTRYPOINT ["/startup.sh"]
