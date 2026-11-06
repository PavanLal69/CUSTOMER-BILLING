FROM node:22-alpine AS frontend-build

WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS app

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VECTOR_BACKEND=sqlite \
    EMBEDDING_BACKEND=hash \
    VECTOR_DIR=/data/vector_store

COPY requirements-light.txt ./
RUN pip install --no-cache-dir -r requirements-light.txt

COPY src/ ./src/
COPY data/ ./data/
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

EXPOSE 8000
CMD ["sh", "-c", "python -m src.ingest --no-reset && exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
