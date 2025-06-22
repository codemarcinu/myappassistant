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
7. [Troubleshooting](#troubleshooting)

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Git

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd my_ai_assistant

# Setup development environment
./scripts/dev-setup.sh

# Start all services
./run_dev.sh
```

### Manual Setup

```bash
# Backend setup
cd src/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend setup
cd foodsave-frontend
npm install

# Database setup
python scripts/seed_db.py
```

## Docker Deployment

### Development Environment

```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Production Environment

```bash
# Build and start production services
docker-compose up -d --build

# Scale services
docker-compose up -d --scale backend=3 --scale frontend=2

# Update services
docker-compose pull
docker-compose up -d
```

### Docker Configuration Files

- `docker-compose.yaml` - Production configuration
- `docker-compose.dev.yml` - Development configuration
- `Dockerfile` - Backend production image
- `Dockerfile.dev` - Backend development image
- `foodsave-frontend/Dockerfile` - Frontend image

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

   # Install Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd my_ai_assistant

   # Configure environment
   cp env.dev.example .env
   # Edit .env with production values

   # Deploy
   docker-compose up -d --build
   ```

3. **SSL Certificate Setup**
   ```bash
   # Install Certbot
   sudo apt install certbot python3-certbot-nginx

   # Generate certificate
   sudo certbot --nginx -d yourdomain.com
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
    server_name yourdomain.com;

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

### Required Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/foodsave
REDIS_URL=redis://localhost:6379

# AI Models
OLLAMA_BASE_URL=http://localhost:11434
OPENAI_API_KEY=your_openai_key

# Security
SECRET_KEY=your_secret_key
JWT_SECRET_KEY=your_jwt_secret

# External Services
WEATHER_API_KEY=your_weather_api_key
GOOGLE_MAPS_API_KEY=your_google_maps_key

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true
```

### Environment File Structure

```
.env
├── .env.production    # Production settings
├── .env.staging      # Staging settings
├── .env.development  # Development settings
└── .env.local        # Local overrides
```

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'foodsave-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  - job_name: 'foodsave-frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/metrics'
```

### Grafana Dashboards

1. **System Overview Dashboard**
   - CPU and memory usage
   - Network traffic
   - Disk I/O

2. **Application Metrics Dashboard**
   - Request rates and response times
   - Error rates
   - AI model performance

3. **Business Metrics Dashboard**
   - User activity
   - Feature usage
   - AI agent performance

### Log Aggregation

```yaml
# Loki configuration
loki:
  config:
    auth_enabled: false
    server:
      http_listen_port: 3100
    ingester:
      lifecycler:
        address: 127.0.0.1
        ring:
          kvstore:
            store: inmemory
          replication_factor: 1
        final_sleep: 0s
      chunk_idle_period: 5m
      chunk_retain_period: 30s
```

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
