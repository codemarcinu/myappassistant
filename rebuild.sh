#!/bin/bash
set -e

echo "=== Rebuilding AI Assistant with GPU Support ==="
echo ""

# Check if NVIDIA Container Toolkit is installed
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️ NVIDIA drivers don't appear to be installed or working properly."
    echo "Please run the setup_nvidia_docker.sh script first."
    exit 1
fi

# Remove existing containers and volumes
echo "Removing existing containers and volumes..."
docker-compose down -v

# Remove existing images
echo "Removing existing images..."
docker image rm -f my_ai_assistant_backend my_ai_assistant_frontend 2>/dev/null || true

# Build new containers with GPU support
echo "Building new containers with GPU support..."
docker-compose build --no-cache

# Start the containers
echo "Starting containers with GPU support..."
docker-compose up -d

echo ""
echo "=== Build completed! ==="
echo "The system is now running with GPU support."
echo ""
echo "Services:"
echo "- Backend: http://localhost:8000"
echo "- Frontend: http://localhost:3000"
echo ""
echo "To view logs, run: docker-compose logs -f"
echo "To stop the system, run: docker-compose down"