FROM python:3.9-slim

WORKDIR /app

COPY services/risk_agent/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r /app/requirements.txt

COPY services/shared /app/services/shared
COPY services/risk_agent /app/services/risk_agent

ENV PYTHONPATH=/app

RUN useradd -m appuser && chown -R appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; import sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8004/health').getcode() == 200 else 1)"

CMD ["uvicorn", "services.risk_agent.main:app", "--host", "0.0.0.0", "--port", "8004"]
