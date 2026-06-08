# Stage 1: Install dependencies
FROM python:3.13-alpine AS deps
WORKDIR /app

# Build tools needed for C extensions (cryptography, argon2-cffi, asyncpg, dependency-injector)
RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev binutils

RUN pip install --no-cache-dir uv
COPY pyproject.toml ./
RUN uv sync --no-dev && \
    find /app/.venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /app/.venv -name "*.so" -exec strip --strip-debug {} + 2>/dev/null || true

# Stage 2: Production image — minimal
FROM python:3.13-alpine AS production
WORKDIR /app

# Runtime libraries only (no build tools)
RUN apk add --no-cache libffi openssl

# Security: non-root user
RUN addgroup -S hiver && adduser -S -G hiver hiver
ENV PASSWORD = "admin123"

# Copy only what's needed from deps stage
COPY --from=deps /app/.venv .venv
COPY src/ src/

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

USER hiver
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
