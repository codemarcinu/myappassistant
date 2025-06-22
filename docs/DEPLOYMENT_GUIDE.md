# FoodSave AI - Deployment Guide

## Overview

This guide covers all deployment scenarios for the FoodSave AI system, from local development to production environments.

## Table of Contents

1. [Local Development Setup](#local-development-setup)
2. [Docker Deployment](#docker-deployment)
3. [Production Deployment](#production-deployment)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring Setup](#monitoring-setup)
6. [Backup and Recovery](#backup-and-recovery)
7. [Troubleshooting](#troubleshooting-deployment)

## Local Development Setup

### Prerequisites

- **Python 3.12+**
- **Node.js 20+**
- **Poetry** for Python package management
- **Ollama** installed and running locally
- **Git**

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/foodsave-ai.git
cd foodsave-ai

# Copy environment variables file
cp env.dev.example .env

# Run the setup and startup script
./run_all.sh
```
This script will check for dependencies, install them if necessary, and start the backend and frontend services.

## Docker Deployment

### Development Environment
This is the recommended method for development as it provides a consistent and complete environment with all services.

```bash
# First, ensure you have an environment file
cp env.dev.example .env

# Build and start development environment
docker-compose -f docker-compose.dev.yml up -d --build

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```
> **Note on PostgreSQL Port:** If you have a local PostgreSQL instance running, you might encounter a port conflict on `5432`. We've already changed the configuration in `docker-compose.dev.yml` to use port **5433** for the container, so this issue should be resolved.

### Production Environment

```bash
# Create a production environment file from the example
cp env.prod.example .env.production
# IMPORTANT: Edit .env.production with your production secrets and configuration

# Build and start production services using the production config
docker-compose up -d --build

# Scale services (example)
docker-compose up -d --scale backend=3 --scale frontend=2

# To update running services
docker-compose pull # Pull the latest images
docker-compose up -d --build # Rebuild and restart services
```

### Docker Configuration Files

- `docker-compose.yaml` - Production configuration
- `docker-compose.dev.yml` - Development configuration
- `Dockerfile` - Backend production image
- `Dockerfile.dev` - Backend development image
- `foodsave-frontend/Dockerfile` - Frontend production image
- `foodsave-frontend/Dockerfile.dev.frontend` - Frontend development image

## Production Deployment

### Server Requirements

- **CPU**: 4+ cores (8+ recommended)
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 100GB+ SSD
- **OS**: Ubuntu 20.04+ or CentOS 8+
- **Network**: Stable internet connection

### Deployment Steps

1. **Server Preparation**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker Engine
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install Docker Compose v2
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd foodsave-ai

   # Configure environment
   cp env.prod.example .env.production
   # IMPORTANT: Edit .env.production with your production values

   # Deploy
   docker-compose up -d --build
   ```

3. **SSL Certificate Setup**
   ```bash
   # Install Certbot
   sudo apt install certbot python3-certbot-nginx

   # Generate certificate
   sudo certbot --nginx -d foodsave.yourdomain.com
   ```

### Load Balancer Configuration

```nginx
# Nginx configuration for load balancing
upstream backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

upstream frontend {
    server frontend1:3000;
    server frontend2:3000;
}

server {
    listen 80;
    server_name foodsave.yourdomain.com;

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Environment Configuration

### Key Environment Variables (`.env` file)

```bash
# --- General Settings ---
ENVIRONMENT=development # or "production"
SECRET_KEY=your_super_secret_key_for_jwt

# --- Database ---
DATABASE_URL=postgresql+asyncpg://foodsave_user:foodsave_password@postgres:5432/foodsave_db # For Docker
# DATABASE_URL=sqlite+aiosqlite:///./foodsave.db # For local setup
REDIS_URL=redis://redis:6379 # For Docker
# REDIS_URL=redis://localhost:6379 # For local setup

# --- AI Models (Ollama) ---
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest
OLLAMA_EMBED_MODEL=nomic-embed-text

# --- External Services (Optional) ---
PERPLEXITY_API_KEY=your_perplexity_api_key_if_used

# --- Monitoring & Telemetry ---
PROMETHEUS_ENABLED=true
TELEMETRY_ENABLED=true
JAEGER_AGENT_HOST=jaeger # For Docker setup

# --- Frontend URL ---
NEXT_PUBLIC_API_URL=http://localhost:8000
```
> This is a sample configuration. Refer to `env.dev.example` for the complete list of variables used in development. Production deployments should use a separate, secured configuration.

## Monitoring Setup
The monitoring stack (Prometheus, Grafana, Loki) is pre-configured in the `docker-compose.dev.yml` file.

### Prometheus Configuration

```yaml
# monitoring/prometheus.dev.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'foodsave-backend'
    # This target points to the backend container within Docker's network
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana Dashboards
Access Grafana at `http://localhost:3001` (user: `admin`, pass: `admin`).

1. **System Overview Dashboard**
   - CPU and memory usage
   - Network traffic and container health
   - Disk I/O

2. **Application Metrics Dashboard**
   - API request rates and response times (latency)
   - HTTP status code distribution (2xx, 4xx, 5xx)
   - Agent performance and execution times

3. **Business Metrics Dashboard**
   - User activity
   - Feature usage
   - AI agent performance

### Log Aggregation (Loki)
Logs from all Docker containers are automatically collected by Promtail and sent to Loki. You can query and view these logs directly in Grafana using the "Loki" data source.

## Backup and Recovery

### Automated Backups

```bash
# Database backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U postgres foodsave > backup_$DATE.sql

# File backup
tar -czf backup_files_$DATE.tar.gz data/ uploads/

# Vector store backup
cp -r vector_store/ backup_vector_store_$DATE/
```

### Recovery Procedures

1. **Database Recovery**
   ```bash
   # Stop services
   docker-compose down

   # Restore database
   docker exec -i postgres psql -U postgres foodsave < backup_20241222_143000.sql

   # Restart services
   docker-compose up -d
   ```

2. **Full System Recovery**
   ```bash
   # Restore from backup
   tar -xzf backup_files_20241222_143000.tar.gz
   cp -r backup_vector_store_20241222_143000/ vector_store/

   # Restart services
   docker-compose up -d
   ```

## Troubleshooting

### Common Issues

1. **Services Not Starting**
   ```bash
   # Check logs
   docker-compose logs [service_name]

   # Check resource usage
   docker stats

   # Restart specific service
   docker-compose restart [service_name]
   ```

2. **Database Connection Issues**
   ```bash
   # Check database status
   docker exec postgres pg_isready

   # Check connection pool
   docker exec backend python -c "from src.backend.infrastructure.database.database import get_db; print(get_db())"
   ```

3. **AI Model Issues**
   ```bash
   # Check Ollama status
   curl http://localhost:11434/api/tags

   # Restart Ollama
   sudo systemctl restart ollama
   ```

### Performance Optimization

1. **Database Optimization**
   ```sql
   -- Add indexes for common queries
   CREATE INDEX idx_receipts_user_id ON receipts(user_id);
   CREATE INDEX idx_conversations_user_id ON conversations(user_id);
   ```

2. **Caching Strategy**
   ```python
   # Redis caching for AI responses
   @cache(expire=3600)
   def get_ai_response(query: str) -> str:
       # AI processing logic
       pass
   ```

3. **Load Balancing**
   ```yaml
   # Docker Compose with multiple instances
   services:
     backend:
       deploy:
         replicas: 3
       environment:
         - WORKER_PROCESSES=4
   ```

### Health Checks

```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {
            "database": check_database(),
            "redis": check_redis(),
            "ollama": check_ollama(),
            "vector_store": check_vector_store()
        }
    }
```

## Security Considerations

### Network Security

- Use HTTPS in production
- Implement rate limiting
- Configure firewall rules
- Use VPN for admin access

### Data Security

- Encrypt sensitive data at rest
- Use secure API keys
- Implement proper authentication
- Regular security audits

### Container Security

- Use non-root users in containers
- Scan images for vulnerabilities
- Keep base images updated
- Implement resource limits

## Maintenance

### Regular Tasks

- **Daily**: Monitor logs and metrics
- **Weekly**: Review performance metrics
- **Monthly**: Update dependencies
- **Quarterly**: Security audit

### Update Procedures

```bash
# Update application
git pull origin main
docker-compose down
docker-compose up -d --build

# Update dependencies
pip install -r requirements.txt --upgrade
npm update

# Database migrations
alembic upgrade head
```

---

**Last Updated**: December 22, 2024
**Version**: 1.0
**Maintainer**: FoodSave AI Team
