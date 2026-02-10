# -----------------------------
# Stage 1: Build React Frontend
# -----------------------------
FROM node:18-slim AS build-frontend

WORKDIR /app_build

# copy full module so dockerignore cannot hide frontend
COPY pdf_search ./pdf_search

WORKDIR /app_build/pdf_search/frontend

RUN npm ci
RUN npm run build


# -----------------------------
# Stage 2: Python Backend
# -----------------------------
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# install backend dependencies
COPY pdf_search/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# copy backend code
COPY pdf_search ./pdf_search

# pre-download embedding model
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='./model_cache')"

# copy built frontend
COPY --from=build-frontend /app_build/pdf_search/frontend/dist ./frontend/dist

EXPOSE 8000

ENV PORT=8000
ENV ENDEE_HOST=host.docker.internal
ENV ENDEE_PORT=8080

ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV ONNXRUNTIME_EXECUTION_MODE=SEQUENTIAL

CMD ["sh", "-c", "uvicorn pdf_search.api:app --host 0.0.0.0 --port ${PORT} --workers 1"]
