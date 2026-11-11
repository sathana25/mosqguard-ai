# One container: builds the React PWA, then serves it and the API with FastAPI.

FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim
# INSTALL_ML=true adds YOLOv8 (CPU PyTorch, about 1 GB). false = basic heuristic detector only.
ARG INSTALL_ML=true
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend

COPY backend/requirements.txt backend/requirements-ml.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALL_ML" = "true" ]; then \
      apt-get update && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/* && \
      pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu && \
      pip install --no-cache-dir -r requirements-ml.txt ; \
    fi

COPY backend/ .
COPY ml/ /app/ml/
COPY --from=web /web/dist /app/frontend/dist

ENV DATABASE_URL=sqlite:////data/mosqguard.db \
    UPLOAD_DIR=/data/uploads \
    STATIC_DIR=/app/frontend/dist \
    YOLO_CONFIG_DIR=/data/yolo
VOLUME /data
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
