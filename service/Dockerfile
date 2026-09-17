FROM python:3.12-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt
COPY service/requirements.lock.txt service/requirements.lock.txt
RUN pip install --no-cache-dir -r service/requirements.lock.txt && pip check
COPY api api
COPY scripts scripts
COPY mcp_layer mcp_layer
COPY service service
COPY analysis analysis
COPY contracts contracts
COPY starter/claims.schema.json starter/claims.schema.json
COPY tests/bootstrap tests/bootstrap
COPY tests/analysis tests/analysis
COPY eval/analysis eval/analysis
COPY tools/bootstrap tools/bootstrap
ENV PYTHONUNBUFFERED=1
EXPOSE 8001
CMD ["uvicorn", "service.main:app", "--host", "0.0.0.0", "--port", "8001"]
