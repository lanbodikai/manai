FROM python:3.12-slim
WORKDIR /app
COPY tools/bootstrap/page /app/page
COPY contracts/examples/audit-response.json /app/fixtures/audit-response.json
EXPOSE 3000
CMD ["python", "/app/page/server.py"]
