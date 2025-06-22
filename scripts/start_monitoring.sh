#!/bin/bash

# Script to start monitoring services for FoodSave AI
# Author: FoodSave AI Team
# Date: 2024

echo "========================================"
echo "Starting FoodSave AI Monitoring Services"
echo "========================================"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not accessible"
    exit 1
fi

# Check if the setup script has been run
if [ ! -d "logs/backend" ] || [ ! -d "logs/frontend" ] || [ ! -d "logs/ollama" ]; then
    echo "Log directories not found. Running setup script first..."
    bash scripts/setup_logging.sh
fi

# Start the monitoring services
echo "Starting monitoring services..."
docker compose -f docker-compose.logging.yml up -d

# Give services time to initialize
echo "Waiting for services to initialize..."
sleep 5

# Check if services are running
if docker ps | grep -q "foodsave-grafana"; then
    echo "Grafana is running"
else
    echo "Error: Grafana failed to start"
fi

if docker ps | grep -q "foodsave-loki"; then
    echo "Loki is running"
else
    echo "Error: Loki failed to start"
fi

if docker ps | grep -q "foodsave-promtail"; then
    echo "Promtail is running"
else
    echo "Error: Promtail failed to start"
fi

echo ""
echo "========================================"
echo "Monitoring services started!"
echo "========================================"
echo "Access Grafana dashboard at: http://localhost:3030"
echo "Username: admin"
echo "Password: foodsave"
echo "========================================"

exit 0 