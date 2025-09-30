# Docker Demo Guide

This guide shows how to run the metadata extractor API and Redis using Docker containers.

## Prerequisites
- Docker and Docker Compose installed
- No need for local Python, Redis, or virtual environments!

## Quick Start

### 1. Build and Start All Services
```bash
# Build the application image and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

This will start:
- **Redis** on port `6379` (with persistent data)
- **Metadata Extractor API** on port `8000`
- **RQ Worker** for background job processing

### 2. Verify Services are Running
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs app
docker-compose logs redis
docker-compose logs worker
```

### 3. Health Check
```bash
curl http://localhost:8000/health
```
Should return `{"status": "ok"}`.

## Demo Workflow

### 1. Seed Redis with Sample Data

**Option A: Run in existing container (while services are running)**
```bash
# In a new terminal, while docker-compose up is running
docker-compose exec app python sample_data/seed_redis.py
```

**Option B: Use the dedicated seeder service**
```bash
# Start all services including the seeder
docker-compose --profile seed up --build

# Or run seeder separately after services are up
docker-compose run --rm seed
```

### 2. Extract Metadata from Redis
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "type": "redis",
      "host": "redis",
      "port": 6379,
      "db": 0,
      "password": null,
      "scan_count": 1000,
      "sample_keys_limit": 5000,
      "include_patterns": ["*"],
      "exclude_patterns": [],
      "prefix_tags": { "user:": "users", "order:": "orders" }
    },
    "flags": { "all": true }
  }'
```

### 3. Test Background Jobs (Async Processing)
```bash
# Submit a job
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "config": { "type": "redis", "host": "redis", "port": 6379, "db": 0 },
    "flags": { "all": true }
  }'

# Poll for results (replace <jobId> with the returned job ID)
curl http://localhost:8000/jobs/<jobId>
```

### 4. Test GitHub Extraction
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config":{
      "type": "github",
      "owner": "pallets",
      "repo": "flask"
    },
    "flags": { "all": true }
}'
```

## Container Management

### View Container Logs
```bash
# Follow logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f app
docker-compose logs -f redis
docker-compose logs -f worker
```

### Execute Commands in Containers
```bash
# Access the app container shell
docker-compose exec app bash

# Access Redis CLI
docker-compose exec redis redis-cli

# Run Python scripts in the app container
docker-compose exec app python sample_data/seed_redis.py
```

### Stop and Clean Up
```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clears Redis data)
docker-compose down -v

# Remove built images as well
docker-compose down --rmi all -v
```

## Development Mode

For development with live code reloading:

```bash
# Create a development override file
cat > docker-compose.override.yml << EOF
version: '3.8'
services:
  app:
    volumes:
      - .:/app
    environment:
      - FLASK_ENV=development
    command: ["python", "-u", "app.py"]
EOF

# Start with development settings
docker-compose up --build
```

## Monitoring Redis

### View Redis Data
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Inside Redis CLI:
# KEYS *              # List all keys
# GET user:1          # Get specific key
# HGETALL user:1      # Get hash data
# INFO keyspace       # View database info
```

### Monitor Redis Activity
```bash
# Monitor Redis commands in real-time
docker-compose exec redis redis-cli MONITOR
```

## Troubleshooting

### Port Conflicts
If ports 6379 or 8000 are already in use:
```bash
# Edit docker-compose.yml and change port mappings:
# "8001:8000" instead of "8000:8000"
# "6380:6379" instead of "6379:6379"
```

### Container Health Issues
```bash
# Check container health
docker-compose ps

# View detailed logs
docker-compose logs app

# Restart specific service
docker-compose restart app
```

### Redis Connection Issues
```bash
# Verify Redis is accessible from app container
docker-compose exec app ping redis

# Check Redis connectivity
docker-compose exec app python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

## Production Considerations

For production deployment:

1. **Environment Variables**: Use `.env` file for sensitive configurations
2. **Resource Limits**: Add memory and CPU limits to services
3. **Security**: Use secrets management for passwords/tokens
4. **Monitoring**: Add health check endpoints and monitoring tools
5. **Scaling**: Use Docker Swarm or Kubernetes for multi-instance deployment

Example production `.env` file:
```bash
REDIS_URL=redis://redis:6379/0
GITHUB_TOKEN=your_github_token_here
FLASK_ENV=production
```
