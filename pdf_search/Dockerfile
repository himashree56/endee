# -----------------------------
# Stage 1: Build React Frontend
# -----------------------------
FROM node:18-slim AS build-frontend

WORKDIR /app_build

# ✅ FIXED PATH (your frontend is inside pdf_search)
COPY pdf_search/frontend ./frontend

WORKDIR /app_build/frontend

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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Pre-download embedding model (BAAI/bge-small-en-v1.5)
RUN python -c "from fastembed import TextEmbedding; TextEmbedding(model_name='BAAI/bge-small-en-v1.5', cache_dir='./model_cache')"

# ✅ Copy built frontend into backend image
COPY --from=build-frontend /app_build/frontend/dist ./frontend/dist

EXPOSE 8000

ENV PORT=8000
ENV ENDEE_HOST=host.docker.internal
ENV ENDEE_PORT=8080

# Memory Optimizations for low RAM environments
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV ONNXRUNTIME_EXECUTION_MODE=SEQUENTIAL

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT} --workers 1"]
