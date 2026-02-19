FROM python:3.9-slim

WORKDIR /app

# Architecture Decision: Single-stage build
# Rationale: All dependencies are pure Python (psycopg2-binary).
# Installing globally to /usr/local via root avoids the complexity
# and permission issues of copying /root/.local/bin artifacts.

COPY services/consensus_agent/requirements.txt /app/requirements.txt

# Install globally to /usr/local/bin
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt

COPY services/shared /app/services/shared
COPY services/consensus_agent /app/services/consensus_agent

ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Python native healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8005/health').getcode() == 200 else 1)"

CMD ["uvicorn", "services.consensus_agent.main:app", "--host", "0.0.0.0", "--port", "8005"]
