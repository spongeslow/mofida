# ── Build stage — compiles the Vite/React SPA into static assets ─────────────
FROM node:20-alpine AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ ./
RUN npm run build

# ── Dev stage — Vite dev server with hot-reload on port 5173 ─────────────────
# Used by docker-compose for local development. The Tauri desktop binary on the
# host connects to this server via localhost:5173 (or http://host.docker.internal:5173
# on macOS/Windows).
FROM node:20-alpine AS dev
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --prefer-offline
COPY frontend/ ./
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# ── Production stage — serves the built SPA via a lightweight HTTP server ─────
FROM node:20-alpine AS prod
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
EXPOSE 5173
CMD ["serve", "-s", "dist", "-l", "5173"]
