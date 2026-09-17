FROM node:22-alpine AS build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY contracts /app/contracts
COPY dashboard /app/dashboard
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
COPY --from=build /app/dashboard/dist /app/dist
COPY dashboard/server.py /app/server.py
ENV PYTHONUNBUFFERED=1
EXPOSE 3000
CMD ["python", "server.py"]
