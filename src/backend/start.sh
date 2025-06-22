#!/bin/sh
set -e

# Check if model exists, if not, download it
if [ ! -d "$HF_HOME/hub/models--sdadas--mmlw-retrieval-roberta-base" ]; then
    echo "Model MMLW not found in cache. Downloading..."
    # Using python to download and cache the model
    python -c "from transformers import AutoModel, AutoTokenizer; AutoTokenizer.from_pretrained('sdadas/mmlw-retrieval-roberta-base'); AutoModel.from_pretrained('sdadas/mmlw-retrieval-roberta-base');"
    echo "Model downloaded successfully."
else
    echo "Model MMLW already exists in cache."
fi

echo "Starting backend server..."
exec uvicorn src.backend.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir /app/src/backend
