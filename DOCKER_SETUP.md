# FoodSave AI - Docker Environment

This document contains instructions for running the FoodSave AI environment using Docker.

## Requirements

- Docker Engine 19.03.0+
- Docker Compose V2
- At least 8GB RAM
- At least 20GB free disk space
- (Optional) NVIDIA GPU with installed NVIDIA Container Toolkit for GPU acceleration

## Environment Structure

The environment consists of the following services:

1. **Backend** - FastAPI application written in Python
2. **Frontend** - Next.js application written in TypeScript
3. **Ollama** - Local language models
4. **PostgreSQL** - Database
5. **Redis** - Caching (optional)
6. **Prometheus** - Metrics collection (optional)
7. **Grafana** - Monitoring dashboard (optional)
8. **Loki** - Log aggregation (optional)
9. **Promtail** - Log collection (optional)

## Management Script

A single management script `foodsave.sh` is provided to manage the environment. This script replaces the previous separate scripts and provides a unified interface for all operations.

### Basic Usage

```bash
# Make the script executable
chmod +x foodsave.sh

# Show help
./foodsave.sh help
```

### Starting the Environment

```bash
# Start core services only (Backend, Frontend, Ollama, PostgreSQL)
./foodsave.sh start

# Start with monitoring services (adds Prometheus and Grafana)
./foodsave.sh start monitoring

# Start with caching services (adds Redis)
./foodsave.sh start cache

# Start with logging services (adds Loki and Promtail)
./foodsave.sh start logging

# Start with all services
./foodsave.sh start all
```

### Checking Status

```bash
./foodsave.sh status
```

This will display:
- List of running containers
- Health status of each service
- URLs and ports for accessing services

### Viewing Logs

```bash
# View logs from all services
./foodsave.sh logs

# View logs from a specific service
./foodsave.sh logs backend
./foodsave.sh logs frontend
./foodsave.sh logs ollama
```

### Stopping the Environment

```bash
./foodsave.sh stop
```

## Service Access

After starting the environment, services are available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434
- **PostgreSQL**: localhost:5433 (user: foodsave, password: foodsave_dev_password)
- **Prometheus**: http://localhost:9090 (when using monitoring profile)
- **Grafana**: http://localhost:3001 (when using monitoring profile)
- **Redis**: localhost:6379 (when using cache profile)
- **Loki**: http://localhost:3100 (when using logging profile)

## Environment Variables

Environment variables are configured in the `.env` file. If this file doesn't exist, it will be created automatically from `env.dev.example` when starting the environment.

Key environment variables:

- `DATABASE_URL` - Database connection URL
- `OLLAMA_URL` - URL to the Ollama service
- `OLLAMA_MODEL` - Ollama model to use
- `NEXT_PUBLIC_API_URL` - Backend URL used by the frontend

## Troubleshooting

### Container Name Conflicts

If you encounter container name conflicts, the `foodsave.sh start` command automatically removes existing containers with the same names before starting new ones.

### Database Connection Issues

If the backend can't connect to the database, check:
1. PostgreSQL is running (`./foodsave.sh status`)
2. The DATABASE_URL environment variable is correctly configured in the `.env` file

### Ollama Connection Issues

If the backend can't connect to Ollama, check:
1. Ollama is running (`./foodsave.sh status`)
2. The OLLAMA_URL environment variable is correctly configured

### Volume Issues

If you experience issues with volumes, you can remove them and recreate them:

```bash
./foodsave.sh stop
docker volume rm foodsave-ai_postgres_data foodsave-ai_ollama_data
./foodsave.sh start
```

## Advanced Configuration

Advanced configuration options can be found in the `docker-compose.yaml` file.

You can customize the Dockerfiles used for building images by setting these environment variables:
- `BACKEND_DOCKERFILE` - Path to the backend Dockerfile (default: Dockerfile)
- `FRONTEND_DOCKERFILE` - Path to the frontend Dockerfile (default: Dockerfile)

## Available Profiles

The Docker Compose configuration includes several profiles that can be activated:

1. **monitoring** - Includes Prometheus and Grafana for metrics collection and visualization
2. **with-cache** - Includes Redis for caching
3. **logging** - Includes Loki and Promtail for centralized logging

You can combine these profiles using the `foodsave.sh start all` command.
