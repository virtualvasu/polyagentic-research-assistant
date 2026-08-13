# Single-container build (currently deployed on Render): a Next.js frontend
# (exposed) reverse-proxying, via its own server-side Route Handlers, to an
# internal FastAPI + LangGraph backend. Two processes, one image, one port.
# Platform-agnostic — no assumptions beyond "give the container a PORT env
# var and route traffic to it," so it runs unchanged on Render, Fly.io, a
# VPS, or locally.

# ---------- Frontend build ----------
FROM node:20-bookworm-slim AS frontend-build
WORKDIR /app/frontend

# better-sqlite3 compiles a native addon at install time.
RUN apt-get update && apt-get install -y --no-install-recommends python3 make g++ \
    && rm -rf /var/lib/apt/lists/*

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npx prisma generate

# Pre-apply migrations to a template DB baked into the image; start.sh
# copies it to the runtime data dir on first boot (see below).
RUN DATABASE_URL="file:./prisma/seed.db" npx prisma migrate deploy

RUN npm run build

# ---------- Final image ----------
FROM python:3.11-slim AS final

RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# --- Backend ---
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/app backend/app

# --- Frontend (Next.js standalone output) ---
COPY --from=frontend-build /app/frontend/.next/standalone ./frontend
COPY --from=frontend-build /app/frontend/.next/static ./frontend/.next/static
COPY --from=frontend-build /app/frontend/public ./frontend/public
COPY --from=frontend-build /app/frontend/prisma/seed.db ./frontend/prisma/seed.db

COPY docker/start.sh /app/start.sh
RUN chmod +x /app/start.sh && mkdir -p /data

ENV BACKEND_URL=http://127.0.0.1:8000 \
    FRONTEND_ORIGIN=http://127.0.0.1:7860 \
    PYTHONUNBUFFERED=1 \
    PORT=7860

# Default port — overridden automatically at runtime by whatever PORT the
# host platform injects (e.g. Render sets PORT=10000; start.sh picks it up).
EXPOSE 7860

CMD ["/app/start.sh"]
