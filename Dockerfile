# =============================================================================
# Production Multi-Stage Dockerfile — Ask My Docs
# =============================================================================
# Runs both FastAPI and Next.js in a single container.
# Process chain: tini (PID 1) -> supervisord -> {uvicorn, node server.js}
# Exposes port 7860 for Hugging Face Spaces.
#
# Build:
#   docker build -t ask-my-docs .
#
# Run:
#   docker run -p 7860:7860 --env-file .env ask-my-docs
# =============================================================================

# ─── Stage 1: Install frontend dependencies ─────────────────────────────────
# node:18-slim is Debian-based (glibc), matching the python:3.11-slim production
# stage. Using Alpine (musl) here would produce a node binary that cannot execute
# in the final image.
FROM node:18-slim AS frontend-deps
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --omit=dev

# ─── Stage 2: Build Next.js in production mode ──────────────────────────────
# standalone output produces a self-contained server.js (~59MB) instead of the
# full node_modules tree (~366MB). This is the single biggest size win.
FROM node:18-slim AS frontend-build
WORKDIR /app/frontend
COPY --from=frontend-deps /app/frontend/node_modules ./node_modules
COPY frontend/ .
ARG BACKEND_URL=http://localhost:8001
ENV BACKEND_URL=${BACKEND_URL}
ARG NEXT_PUBLIC_API_URL=/api
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
RUN npm run build

# ─── Stage 3: Install Python dependencies ───────────────────────────────────
# Install into a virtual env at /opt/venv so the entire Python dependency tree
# is self-contained and can be copied as a single layer.
FROM python:3.11-slim AS python-deps
WORKDIR /app
COPY requirements.txt .
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt

# ─── Stage 4: Production image ──────────────────────────────────────────────
FROM python:3.11-slim AS production

# --- System deps: tini (init) + curl (healthcheck) ---
RUN apt-get update && \
    apt-get install -y --no-install-recommends tini curl && \
    rm -rf /var/lib/apt/lists/*

# --- Copy Python virtual env from python-deps stage ---
COPY --from=python-deps /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# --- Copy Node.js runtime from frontend-deps stage ---
# Both stages use Debian (glibc), so the binary and native modules are compatible.
COPY --from=frontend-deps /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend-deps /app/frontend/node_modules /app/frontend/node_modules

# --- Copy built Next.js from frontend-build stage ---
COPY --from=frontend-build /app/frontend/.next/standalone /app/frontend/
COPY --from=frontend-build /app/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-build /app/frontend/public /app/frontend/public

# --- Copy backend application code ---
WORKDIR /app
COPY src/ src/
COPY scripts/ scripts/

# --- Copy pre-built indexes (optional, for pre-loaded demo) ---
COPY storage/ storage/
COPY data/ data/

# --- Application configuration ---
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV API_HOST=0.0.0.0
ENV API_PORT=8001

# --- Install supervisord to manage both processes ---
RUN pip install --no-cache-dir supervisor

# --- Supervisor configuration ---
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# --- Hugging Face Spaces uses port 7860 ---
ENV PORT=7860
ENV HOSTNAME=0.0.0.0
EXPOSE 7860

# --- Health check: verify both FastAPI and Next.js are responding ---
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s --retries=3 \
    CMD curl -f http://localhost:8001/health && curl -s -o /dev/null -w "%{http_code}" http://localhost:7860/ | grep -q 200 || exit 1

ENTRYPOINT ["tini", "--"]
CMD ["/usr/local/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
