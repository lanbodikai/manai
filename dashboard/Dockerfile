# Build from the repository root so runtime validators use the agreed contract.
FROM node:22.14.0-alpine AS build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY contracts/ /app/contracts/
COPY dashboard/ ./
# The normal build selects HTTP mode and rejects mock modules/fixture markers.
RUN npm run build

FROM nginx:1.27.5-alpine AS runtime
COPY dashboard/nginx.conf /etc/nginx/conf.d/default.conf
# No source fixtures, developer tooling, data, or node_modules enter this stage.
COPY --from=build /app/dashboard/dist/ /usr/share/nginx/html/
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1:3000/ || exit 1
