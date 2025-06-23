#!/bin/bash

# FoodSave AI - Rebuild with Pre-loaded Models Script
# Ten skrypt przebudowuje obraz Docker z pre-pobranymi modelami AI

# Set the base directory to the script's location
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
cd "$BASE_DIR"

# Print header
echo "=================================================="
echo "  FoodSave AI - Rebuild with Pre-loaded Models    "
echo "=================================================="
echo "This will rebuild the Docker image with AI models pre-downloaded"
echo "This may take several minutes on first run..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check if NVIDIA GPU is available
if command -v nvidia-smi &> /dev/null; then
  echo "✅ NVIDIA GPU detected"
  nvidia-smi
  USE_GPU=true
else
  echo "⚠️ NVIDIA GPU not detected, will use CPU only"
  USE_GPU=false
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.yaml down

# Remove old images to force rebuild
echo "🗑️  Removing old backend image..."
docker rmi my_ai_assistant_backend_1 2>/dev/null || true

# Rebuild with pre-loaded models
echo "🔨 Rebuilding backend with pre-loaded models..."
echo "This will download the following models:"
echo "- MMLW embedding model (~248MB)"
echo "- Bielik-4.5B-v3.0-Instruct model"
echo "- gemma3:12b model"
echo "- nomic-embed-text model"
echo ""

# Build the backend image
docker-compose -f docker-compose.yaml build backend

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Backend rebuilt successfully with pre-loaded models!"
    echo ""
    echo "🚀 Starting services..."
    docker-compose -f docker-compose.yaml up -d

    echo ""
    echo "=================================================="
    echo "✅ Rebuild completed successfully!"
    echo "=================================================="
    echo "Access Information:"
    echo "* Backend API: http://localhost:8000"
    echo "* Frontend App: http://localhost:3000"
    echo "* Prometheus: http://localhost:9090"
    echo "* Grafana: http://localhost:3001 (admin/admin)"
    echo "=================================================="
else
    echo ""
    echo "❌ Rebuild failed! Check the error messages above."
    exit 1
fi
