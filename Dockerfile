# PharmaAssist: one container serving the API (/health, /ask, /ask/stream) and the Next.js UI (/).
#   docker build -t agent . && docker run -p 8000:8000 --env-file .env agent

# --- Stage 1: Next.js static export -> /web/out --------------------------------------------------
FROM node:22.23.5-alpine3.24 AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# --- Stage 2: FastAPI + agent -------------------------------------------------------------------
FROM python:3.12.16-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.11.29 /uv /bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
# Dependencies first (exact versions from uv.lock) so code changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Same layout as the repo: config.py resolves corpus/, .cache/ and frontend/out from /app.
COPY backend/ backend/
COPY corpus/ corpus/
COPY --from=web /web/out frontend/out

# Non-root. The embedding cache (.cache/) is built at startup in the background (~25 s, /health stays
# 200 meanwhile), so the image holds no API key and no data derived from one.
RUN useradd --uid 1001 --no-create-home app && mkdir .cache && chown app .cache
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]
# One worker: the index lives in process memory (a second worker would build its own copy).
CMD ["uvicorn", "pharma_assist.api:app", "--host", "0.0.0.0", "--port", "8000"]
