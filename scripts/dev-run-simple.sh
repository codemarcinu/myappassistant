#!/bin/bash

# FoodSave AI - Simple Development Environment Startup Script
# This script starts the development environment with minimal components

# Set the base directory to the script's location
BASE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/.."
cd "$BASE_DIR"

# Create necessary directories
mkdir -p logs/{backend,frontend,nginx,ollama,redis,postgres}
mkdir -p data
mkdir -p backups/{config,database,files,vector_store}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker and try again."
  exit 1
fi

# Check if docker-compose exists
if ! command -v docker-compose &> /dev/null; then
  echo "docker-compose could not be found. Please install it and try again."
  exit 1
fi

# Print header
echo "=================================================="
echo "  FoodSave AI - Development Environment Startup   "
echo "=================================================="
echo "Starting services with monitoring and logging..."

# Stop any existing containers
docker-compose -f docker-compose.dev.yml down

# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Print service status
echo -e "\nService Status:"
docker-compose -f docker-compose.dev.yml ps

# Print access information
echo -e "\n=================================================="
echo "Access Information:"
echo "* Backend API: http://localhost:8000"
echo "* Frontend App: http://localhost:3000"
echo "* Prometheus: http://localhost:9090"
echo "* Grafana: http://localhost:3001 (admin/admin)"
echo "* Loki: http://localhost:3100"
echo "=================================================="
echo -e "\nTo view logs, run: docker-compose -f docker-compose.dev.yml logs -f [service]"
echo "To stop all services, run: docker-compose -f docker-compose.dev.yml down"
echo "=================================================="
