FROM python:3.11-slim

WORKDIR /app

RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# sentence-transformers needs gcc, curl for Docker health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Install heavy dependencies FIRST to cache the Docker layer
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 2. Copy dependencies file
COPY requirements.txt .
# 3. Install remaining dependencies
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Set huggingface cache globally for both build and runtime
ENV HF_HOME=/tmp/huggingface_cache

# Bake AI Models into image (Takes time but prevents runtime hangs)
COPY download_model.py .
RUN mkdir -p /tmp/huggingface_cache && chmod 777 /tmp/huggingface_cache && python download_model.py

COPY . .

USER appuser

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
