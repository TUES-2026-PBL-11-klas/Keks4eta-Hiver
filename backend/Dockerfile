# Stage 1: Install dependencies only
FROM python:3.12-slim AS deps
WORKDIR /app
RUN pip install uv
COPY pyproject.toml ./
RUN uv sync --no-dev

# Stage 2: Production image — minimal
FROM python:3.12-slim AS production
WORKDIR /app

# Security: non-root user
RUN groupadd -r hiver && useradd -r -g hiver hiver

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
