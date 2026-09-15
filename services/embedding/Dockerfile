FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch -- keine CUDA-Bibliotheken
RUN pip install --upgrade pip && \
    pip install \
      --index-url https://download.pytorch.org/whl/cpu \
      torch==2.9.1 \
      torchvision==0.24.1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY app.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1"]
