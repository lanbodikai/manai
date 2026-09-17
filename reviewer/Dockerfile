FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY reviewer/requirements.lock.txt /app/reviewer/requirements.lock.txt
RUN pip install --no-cache-dir -r reviewer/requirements.lock.txt \
    && useradd --uid 10001 --create-home reviewer
COPY contracts /app/contracts
COPY api /app/api
COPY mcp_layer /app/mcp_layer
COPY reviewer /app/reviewer
USER reviewer
EXPOSE 8002
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/health', timeout=2)"
CMD ["python", "-m", "uvicorn", "reviewer.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
