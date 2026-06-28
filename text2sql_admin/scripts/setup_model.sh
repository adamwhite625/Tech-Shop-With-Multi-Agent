#!/bin/bash
# =============================================================
# Setup script: Import the GGUF model into Ollama
# Run this AFTER docker-compose up, when Ollama container is running.
#
# Usage:
#   chmod +x scripts/setup_model.sh
#   ./scripts/setup_model.sh
# =============================================================

set -e

MODEL_NAME="text2sql-12k"
GGUF_FILE="model-12k/gemma-2-2b-it.Q4_K_M.gguf"
CONTAINER_NAME="text2sql-ollama"

echo "=== Text2SQL Model Setup ==="
echo ""

# Check if GGUF file exists
if [ ! -f "$GGUF_FILE" ]; then
    echo "Error: Model file not found at $GGUF_FILE"
    echo "Run 'python download_model.py' first to download the model."
    exit 1
fi

# Check if Ollama container is running
if ! docker ps --format '{{.Names}}' | grep -q "$CONTAINER_NAME"; then
    echo "Error: Ollama container '$CONTAINER_NAME' is not running."
    echo "Run 'docker-compose up -d ollama' first."
    exit 1
fi

echo "1. Copying model file to Ollama container..."
docker cp "$GGUF_FILE" "$CONTAINER_NAME:/tmp/model.gguf"

echo "2. Creating Modelfile..."
docker exec "$CONTAINER_NAME" bash -c 'echo "FROM /tmp/model.gguf" > /tmp/Modelfile'

echo "3. Creating model '$MODEL_NAME' in Ollama..."
docker exec "$CONTAINER_NAME" ollama create "$MODEL_NAME" -f /tmp/Modelfile

echo "4. Cleaning up temp files..."
docker exec "$CONTAINER_NAME" rm -f /tmp/model.gguf /tmp/Modelfile

echo ""
echo "=== Done! Model '$MODEL_NAME' is ready. ==="
echo "Test with: docker exec $CONTAINER_NAME ollama list"
