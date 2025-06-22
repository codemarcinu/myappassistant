#!/bin/bash

# FoodSave AI - Development Docker Setup Script
# This script runs the FoodSave AI application in development mode using Docker Compose

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "  FoodSave AI - Development Docker Setup Script"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Create necessary directories
echo "Creating log directories..."
mkdir -p logs/backend logs/frontend logs/ollama logs/postgres logs/nginx

# Check if .env file exists, if not create it from example
if [ ! -f .env ]; then
  echo "Creating .env file from env.dev.example..."
  cp env.dev.example .env
  echo "Please review and update the .env file with your configuration."
fi

# Check for existing containers with the same names and remove them
echo "Checking for existing containers..."
CONTAINERS=("foodsave-backend-dev" "foodsave-frontend-dev" "foodsave-ollama-dev" "foodsave-postgres-dev")

for container in "${CONTAINERS[@]}"; do
  if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
    echo "Removing existing container: ${container}"
    docker rm -f "${container}" > /dev/null 2>&1 || true
  fi
done

# Stop any existing Docker Compose services
echo "Stopping any existing Docker Compose services..."
docker compose -f docker-compose.dev.yaml down

# Pull latest images
echo "Pulling latest Docker images..."
docker compose -f docker-compose.dev.yaml pull

# Build and start containers
echo "Building and starting containers..."
docker compose -f docker-compose.dev.yaml up --build -d

# Display status
echo "=================================================="
echo "  FoodSave AI Development Environment"
echo "=================================================="
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:8000"
echo "Ollama: http://localhost:11434"
echo "PostgreSQL: localhost:5433"
echo ""
echo "To view logs:"
echo "  docker compose -f docker-compose.dev.yaml logs -f"
echo ""
echo "To stop the environment:"
echo "  docker compose -f docker-compose.dev.yaml down"
echo "=================================================="

# Show running containers
docker compose -f docker-compose.dev.yaml ps

