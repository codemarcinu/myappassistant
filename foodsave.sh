#!/bin/bash

# FoodSave AI - Management Script
# This script provides commands to manage the FoodSave AI application

set -e  # Exit immediately if a command exits with a non-zero status

# Display banner
display_banner() {
  echo "=================================================="
  echo "  FoodSave AI - Management Script"
  echo "=================================================="
}

# Check if Docker is running
check_docker() {
  if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker and try again."
    exit 1
  fi
}

# Start the application
start_app() {
  display_banner
  check_docker

  # Create necessary directories
  echo "Creating log directories..."
  mkdir -p logs/backend logs/frontend logs/ollama logs/postgres logs/redis logs/nginx

  # Check if .env file exists, if not create it from example
  if [ ! -f .env ]; then
    echo "Creating .env file from env.dev.example..."
    cp env.dev.example .env
    echo "Please review and update the .env file with your configuration."
  fi

  # Check for existing containers with the same names and remove them
  echo "Checking for existing containers..."
  CONTAINERS=("foodsave-backend" "foodsave-frontend" "foodsave-ollama" "foodsave-postgres" "foodsave-redis")

  for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
      echo "Removing existing container: ${container}"
      docker rm -f "${container}" > /dev/null 2>&1 || true
    fi
  done

  # Stop any existing Docker Compose services
  echo "Stopping any existing Docker Compose services..."
  docker compose down --remove-orphans

  # Pull latest images
  echo "Pulling latest Docker images..."
  docker compose pull

  # Build and start containers
  echo "Building and starting containers..."
  if [ "$1" == "monitoring" ]; then
    docker compose --profile monitoring up --build -d
    echo "Started with monitoring services"
  elif [ "$1" == "cache" ]; then
    docker compose --profile with-cache up --build -d
    echo "Started with caching services"
  elif [ "$1" == "logging" ]; then
    docker compose --profile logging up --build -d
    echo "Started with logging services"
  elif [ "$1" == "all" ]; then
    docker compose --profile monitoring --profile with-cache --profile logging up --build -d
    echo "Started with all services"
  else
    docker compose up --build -d
    echo "Started with core services only"
  fi

  # Display status
  echo "=================================================="
  echo "  FoodSave AI Development Environment"
  echo "=================================================="
  echo "Frontend: http://localhost:3000"
  echo "Backend API: http://localhost:8000"
  echo "API Docs: http://localhost:8000/docs"
  echo "Ollama: http://localhost:11434"
  echo "PostgreSQL: localhost:5433"

  if [ "$1" == "monitoring" ] || [ "$1" == "all" ]; then
    echo "Prometheus: http://localhost:9090"
    echo "Grafana: http://localhost:3001"
  fi

  if [ "$1" == "logging" ] || [ "$1" == "all" ]; then
    echo "Loki: http://localhost:3100"
  fi

  echo ""
  echo "To view logs:"
  echo "  docker compose logs -f"
  echo ""
  echo "To stop the environment:"
  echo "  ./foodsave.sh stop"
  echo "=================================================="

  # Show running containers
  docker compose ps
}

# Stop the application
stop_app() {
  display_banner
  check_docker

  echo "Stopping containers..."
  docker compose down --remove-orphans

  # Check for any remaining containers
  CONTAINERS=("foodsave-backend" "foodsave-frontend" "foodsave-ollama" "foodsave-postgres" "foodsave-redis")

  for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format '{{.Names}}' | grep -q "^${container}$"; then
      echo "Removing remaining container: ${container}"
      docker rm -f "${container}" > /dev/null 2>&1 || true
    fi
  done

  echo "=================================================="
  echo "  Environment stopped successfully"
  echo "=================================================="
}

# Show status of the application
show_status() {
  display_banner
  check_docker

  # Show running containers
  echo "Running containers:"
  docker compose ps

  # Check service health
  echo -e "\nService health status:"

  # Check backend
  if docker ps --filter "name=foodsave-backend" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Backend: Running"
    echo "   API URL: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
  else
    echo "❌ Backend: Not running"
  fi

  # Check frontend
  if docker ps --filter "name=foodsave-frontend" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Frontend: Running"
    echo "   URL: http://localhost:3000"
  else
    echo "❌ Frontend: Not running"
  fi

  # Check Ollama
  if docker ps --filter "name=foodsave-ollama" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Ollama: Running"
    echo "   URL: http://localhost:11434"
  else
    echo "❌ Ollama: Not running"
  fi

  # Check PostgreSQL
  if docker ps --filter "name=foodsave-postgres" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ PostgreSQL: Running"
    echo "   Port: 5433"
  else
    echo "❌ PostgreSQL: Not running"
  fi

  # Check Redis
  if docker ps --filter "name=foodsave-redis" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Redis: Running"
    echo "   Port: 6379"
  else
    echo "❌ Redis: Not running"
  fi

  # Check Prometheus
  if docker ps --filter "name=foodsave-prometheus" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Prometheus: Running"
    echo "   URL: http://localhost:9090"
  else
    echo "❌ Prometheus: Not running"
  fi

  # Check Grafana
  if docker ps --filter "name=foodsave-grafana" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Grafana: Running"
    echo "   URL: http://localhost:3001"
  else
    echo "❌ Grafana: Not running"
  fi

  # Check Loki
  if docker ps --filter "name=foodsave-loki" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Loki: Running"
    echo "   URL: http://localhost:3100"
  else
    echo "❌ Loki: Not running"
  fi

  # Check Promtail
  if docker ps --filter "name=foodsave-promtail" --format "{{.Status}}" | grep -q "Up"; then
    echo "✅ Promtail: Running"
  else
    echo "❌ Promtail: Not running"
  fi

  echo -e "\nTo view logs:"
  echo "  docker compose logs -f"
  echo -e "\nTo restart services:"
  echo "  ./foodsave.sh start"
  echo -e "\nTo stop services:"
  echo "  ./foodsave.sh stop"
  echo "=================================================="
}

# Show logs
show_logs() {
  display_banner
  check_docker

  if [ -z "$1" ]; then
    echo "Showing logs for all services..."
    docker compose logs -f
  else
    echo "Showing logs for $1..."
    docker compose logs -f "$1"
  fi
}

# Show help
show_help() {
  display_banner
  echo "Usage: ./foodsave.sh [command] [options]"
  echo ""
  echo "Commands:"
  echo "  start [option]    Start the application"
  echo "                    Options: monitoring, cache, logging, all (default: core services only)"
  echo "  stop              Stop the application"
  echo "  status            Show status of the application"
  echo "  logs [service]    Show logs (all services or specific service)"
  echo "  help              Show this help message"
  echo ""
  echo "Examples:"
  echo "  ./foodsave.sh start            # Start core services"
  echo "  ./foodsave.sh start monitoring # Start with monitoring services"
  echo "  ./foodsave.sh start cache      # Start with caching services"
  echo "  ./foodsave.sh start logging    # Start with logging services"
  echo "  ./foodsave.sh start all        # Start with all services"
  echo "  ./foodsave.sh stop             # Stop all services"
  echo "  ./foodsave.sh status           # Show status"
  echo "  ./foodsave.sh logs             # Show all logs"
  echo "  ./foodsave.sh logs backend     # Show backend logs only"
  echo "=================================================="
}

# Main script logic
case "$1" in
  start)
    start_app "$2"
    ;;
  stop)
    stop_app
    ;;
  status)
    show_status
    ;;
  logs)
    show_logs "$2"
    ;;
  help)
    show_help
    ;;
  *)
    show_help
    ;;
esac
