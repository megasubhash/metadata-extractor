# Data Source Application

A pluggable metadata extractor that connects to a data source and extracts:

- Schema metadata: structural overview of the source
- Business context: human-friendly descriptions/tags
- Optional quality metrics: basic data quality indicators
- Optional lineage: data relationships and dependencies

Built with Strategy + Factory patterns for extensibility.

See also:
- `architecture.md` for a high-level overview and diagrams.
- `demo.md` for end-to-end demo steps.

### Background Jobs (Overview)

- Use the Jobs API to run extractions asynchronously via RQ (Redis Queue) or an in-memory fallback.
- Quick start:
  ```bash
  # Terminal 1: start API
  python app.py

  # Terminal 2: start RQ worker (optional but recommended)
  rq worker extract

  # Submit a job
  curl -X POST http://localhost:8000/jobs \
    -H "Content-Type: application/json" \
    -d '{
      "config": { "type": "redis", "host": "localhost", "port": 6379, "db": 0 },
      "flags": { "all": true }
    }'

  # Poll job status
  curl http://localhost:8000/jobs/<jobId>
  ```

## Design

1. Create and activate a virtualenv (Python 3.11+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Run the API server (Flask)

```bash
python app.py
```

Server listens on `http://localhost:8000`.

### Jobs API (Async)

- Submit a background extraction job:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "config": { "type": "redis", "host": "localhost", "port": 6379, "db": 0 },
    "flags": { "all": true }
  }'
```
Response: `{ "jobId": "<id>", "backend": "rq"|"memory" }`

- Poll job status/result:

```bash
curl http://localhost:8000/jobs/<id>
```

- Optional RQ worker (recommended):
  - Ensure Redis is running (or set `REDIS_URL`).
  - In a new terminal from repo root:
    ```bash
    rq worker extract
    ```
  - The API enqueues `jobs.tasks.task_extract` to the `extract` queue.

## GitHub API Source

1. Prepare config (inline in API request) and set `GITHUB_TOKEN` env var if needed.

```yaml
type: github
owner: octocat
repo: Hello-World
# token: ghp_xxx  # or use env var GITHUB_TOKEN
api_base: https://api.github.com
```

2. Call the API:

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

## Redis Source

- **Config example**: `datasource/redis/config.example.yaml`

```yaml
type: redis
host: localhost
port: 6379
db: 0
password: null

# Extraction options
scan_count: 1000
sample_keys_limit: 5000
include_patterns:
  - "*"
exclude_patterns: []

# Business context: map key prefixes to tags
prefix_tags:
  "user:": "users"
  "order:": "orders"
```

2. Call the API:

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
{{ ... }}
