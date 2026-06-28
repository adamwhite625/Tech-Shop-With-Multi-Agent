# ---- Backend (FastAPI) ----
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY api.py .
COPY app.py .
COPY model_client.py .
COPY download_model.py .
COPY example_data/ ./example_data/

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
