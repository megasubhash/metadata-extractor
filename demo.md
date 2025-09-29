# Demo Instructions

This guide shows how to run the API, seed sample data (Redis), and test the extractors via HTTP.

## Prerequisites
- Python 3.11+
- Virtualenv activated
- Dependencies installed: `pip install -r requirements.txt`
- Redis running locally (e.g., `docker run -p 6379:6379 redis:7`)

## 1) Start the API server
```bash
python app.py
```
Server starts on `http://localhost:8000`.

## 2) Seed Redis with sample data (optional but recommended)
Use the provided script `sample_data/seed_redis.py`.
```bash
python sample_data/seed_redis.py
```
This creates a small keyspace across types and prefixes (`user:*`, `order:*`, etc.).

## 3) Extract from Redis
Send a POST request to `/extract` with a minimal inline config and `flags`.
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "type": "redis",
      "host": "localhost",
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
You should see JSON with `schema`, `business_context`, `quality_metrics`, and `lineage` (empty for Redis).

## 3b) Run via Jobs API (async)
Submit a background job and poll for result.

```bash
# Submit
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "config": { "type": "redis", "host": "localhost", "port": 6379, "db": 0 },
    "flags": { "all": true }
  }'

# Poll
curl http://localhost:8000/jobs/<jobId>
```

Optional: start an RQ worker to process jobs via Redis queue `extract`:
```bash
rq worker extract
```

## 4) Extract from GitHub
Optionally test GitHub (public repo shown; token recommended via env `GITHUB_TOKEN`).
```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      "type": "github",
      "owner": "octocat",
      "repo": "Hello-World"
    },
    "flags": { "all": true }
  }'
```
You should see repo `schema` (field lists), `business_context` (description, topics), `quality_metrics` (stars, PR/issue counts), and fork-based `lineage`.

## 5) Optional: Publish to OpenMetadata
If you have an OpenMetadata instance and want to publish Postgres metadata (or attach tags), install the optional client and provide config.
```bash
pip install "openmetadata-ingestion>=1.3,<2"
```
Example request body fields (add to the `/extract` POST body when you also include the Postgres config):
```json
{
  "publishOpenMetadata": true,
  "openMetadataConfig": {
    "server": "http://localhost:8585/api",
    "auth_provider": "no-auth",
    "jwt_token": "",
    "service": {
      "name": "local_pg",
      "type": "Postgres",
      "connection": {
        "hostPort": "localhost:5432",
        "database": "sample_db",
        "username": "sample_user",
        "password": "sample_password"
      }
    }
  }
}
```
Note: This is optional; the core demo works without it.

## 6) Health Check
```bash
curl http://localhost:8000/health
```
Should return `{ "status": "ok" }`.

## Troubleshooting
- If the server fails to start due to `Jinja2/MarkupSafe` imports, ensure pinned versions from `requirements.txt` are installed.
- For Redis connection errors, verify the container/process is up and port `6379` is reachable.
- For GitHub rate limits, set a `GITHUB_TOKEN` env var.
