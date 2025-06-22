#!/bin/bash

# FoodSave AI - Development Environment Status
# This script shows the status of the FoodSave AI development environment

# Display banner
echo "=================================================="
echo "  FoodSave AI - Development Environment Status"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Show running containers
echo "Running containers:"
docker compose -f docker-compose.dev.yaml ps

# Check service health
echo -e "\nService health status:"

# Check backend
if docker ps --filter "name=foodsave-backend-dev" --format "{{.Status}}" | grep -q "Up"; then
  echo "✅ Backend: Running"
  echo "   API URL: http://localhost:8000"
  echo "   API Docs: http://localhost:8000/docs"
else
  echo "❌ Backend: Not running"
fi

# Check frontend
if docker ps --filter "name=foodsave-frontend-dev" --format "{{.Status}}" | grep -q "Up"; then
  echo "✅ Frontend: Running"
  echo "   URL: http://localhost:3000"
else
  echo "❌ Frontend: Not running"
fi

# Check Ollama
if docker ps --filter "name=foodsave-ollama-dev" --format "{{.Status}}" | grep -q "Up"; then
  echo "✅ Ollama: Running"
  echo "   URL: http://localhost:11434"
else
  echo "❌ Ollama: Not running"
fi

# Check PostgreSQL
if docker ps --filter "name=foodsave-postgres-dev" --format "{{.Status}}" | grep -q "Up"; then
  echo "✅ PostgreSQL: Running"
  echo "   Port: 5433"
else
  echo "❌ PostgreSQL: Not running"
fi

echo -e "\nTo view logs:"
echo "  docker compose -f docker-compose.dev.yaml logs -f"
echo -e "\nTo restart services:"
echo "  ./run_dev_docker.sh"
echo -e "\nTo stop services:"
echo "  ./stop_dev_docker.sh"
echo "=================================================="

