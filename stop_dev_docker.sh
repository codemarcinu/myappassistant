#!/bin/bash

# FoodSave AI - Stop Development Docker Environment
# This script stops the FoodSave AI application in development mode

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
echo "=================================================="
echo "  FoodSave AI - Stopping Development Environment"
echo "=================================================="

# Stop containers
echo "Stopping containers..."
docker compose -f docker-compose.dev.yaml down --remove-orphans

# Check for any remaining containers
CONTAINERS=("foodsave-backend-dev" "foodsave-frontend-dev" "foodsave-ollama-dev" "foodsave-postgres-dev")

for container in "${CONTAINERS[@]}"; do
  if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
    echo "Removing remaining container: ${container}"
    docker rm -f "${container}" > /dev/null 2>&1 || true
  fi
done

echo "=================================================="
echo "  Development environment stopped successfully"
echo "=================================================="

