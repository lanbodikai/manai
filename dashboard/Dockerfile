FROM node:22-alpine AS build
WORKDIR /app/dashboard
COPY dashboard/package.json dashboard/package-lock.json ./
RUN npm ci
COPY contracts /app/contracts
COPY dashboard /app/dashboard
ENV VITE_DATASET_API_ENABLED=true
RUN npm run build

FROM node:22-alpine
WORKDIR /app
COPY --from=build /app/dashboard/dist /app/dist
COPY dashboard/package.json /app/package.json
COPY dashboard/server.mjs /app/server.mjs
COPY dashboard/tools/dataset-handler.ts dashboard/tools/decision-summary.ts /app/tools/
COPY dashboard/src/dataset-fields.ts dashboard/src/optimization-options.ts dashboard/src/format.ts /app/src/
EXPOSE 3000
CMD ["node", "--experimental-strip-types", "server.mjs"]
