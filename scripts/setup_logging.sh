#!/bin/bash

# Script to set up logging directories and configuration for FoodSave AI
# Author: FoodSave AI Team
# Date: 2024

echo "========================================"
echo "Setting up logging infrastructure"
echo "========================================"

# Create log directories
echo "Creating log directories..."
mkdir -p logs/backend
mkdir -p logs/frontend
mkdir -p logs/nginx
mkdir -p logs/ollama
mkdir -p logs/redis
mkdir -p logs/postgres

# Ensure the monitoring directory structure exists
echo "Checking monitoring directory structure..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/loki-data
mkdir -p monitoring/grafana-data

# Set permissions
echo "Setting permissions..."
chmod -R 777 logs/
chmod -R 777 monitoring/loki-data
chmod -R 777 monitoring/grafana-data

# Check for required files
echo "Checking for required configuration files..."
if [ ! -f monitoring/loki-config.yaml ]; then
    echo "Error: monitoring/loki-config.yaml not found!"
    exit 1
fi

if [ ! -f monitoring/promtail-config.yaml ]; then
    echo "Error: monitoring/promtail-config.yaml not found!"
    exit 1
fi

if [ ! -f monitoring/grafana/datasources/loki.yml ]; then
    echo "Error: monitoring/grafana/datasources/loki.yml not found!"
    exit 1
fi

if [ ! -f monitoring/grafana/dashboards/dashboards.yml ]; then
    echo "Error: monitoring/grafana/dashboards/dashboards.yml not found!"
    exit 1
fi

if [ ! -f monitoring/grafana/dashboards/foodsave-logs-dashboard.json ]; then
    echo "Error: monitoring/grafana/dashboards/foodsave-logs-dashboard.json not found!"
    exit 1
fi

# Create a simple test log for each service
echo "Creating test logs..."
echo "[$(date)] INFO: Test log entry for backend" > logs/backend/test.log
echo "[$(date)] INFO: Test log entry for frontend" > logs/frontend/test.log
echo "[$(date)] INFO: Test log entry for nginx" > logs/nginx/test.log
echo "[$(date)] INFO: Test log entry for ollama" > logs/ollama/test.log

# Stop existing containers if running
echo "Stopping existing logging containers if running..."
docker compose -f docker-compose.logging.yml down

# Start logging stack
echo "Starting logging stack..."
docker compose -f docker-compose.logging.yml up -d

# Wait for services to initialize
echo "Waiting for services to initialize..."
sleep 10

# Check if services are running
if docker ps | grep -q "foodsave-grafana"; then
    echo "✓ Grafana is running"
else
    echo "✗ Grafana failed to start - check logs with: docker logs foodsave-grafana"
fi

if docker ps | grep -q "foodsave-loki"; then
    echo "✓ Loki is running"
else
    echo "✗ Loki failed to start - check logs with: docker logs foodsave-loki"
fi

if docker ps | grep -q "foodsave-promtail"; then
    echo "✓ Promtail is running"
else
    echo "✗ Promtail failed to start - check logs with: docker logs foodsave-promtail"
fi

# Provide information
echo ""
echo "========================================"
echo "Logging setup complete!"
echo "========================================"
echo "Access Grafana at: http://localhost:3030"
echo "Default credentials:"
echo "  - Username: admin"
echo "  - Password: foodsave"
echo ""
echo "Loki API: http://localhost:3100"
echo "========================================"

exit 0
