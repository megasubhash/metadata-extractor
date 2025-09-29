# Atlan Take-Home: Data Source Application

A pluggable metadata extractor that connects to a data source and extracts:

- Schema metadata: structural overview of the source
- Business context: human-friendly descriptions/tags
- Optional quality metrics: basic data quality indicators
- Optional lineage: data relationships and dependencies

Built with Strategy + Factory patterns for extensibility.

## Project Structure

/atlan-data-source-app/
├── datasource/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── github/
│   │   ├── __init__.py
│   │   ├── strategy.py
│   │   └── config.example.yaml
│   └── redis/
│       ├── __init__.py
│       ├── strategy.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── schema.py
│       │   ├── business.py
│       │   └── quality.py
│       └── config.example.yaml
├── integrations/
│   └── openmetadata_adapter.py   # optional, only if publishing to OpenMetadata
├── sample_data/
│   └── seed_redis.py
├── app.py                        # Flask API entrypoint
├── requirements.txt
├── README.md
└── THOUGHT_PROCESS.md

## Setup

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
