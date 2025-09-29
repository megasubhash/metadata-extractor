# Atlan Take-Home: Data Source Application

A pluggable metadata extractor that connects to a data source (PostgreSQL to start) and extracts:

- Schema metadata: tables, columns, data types, and constraints (PK, FK, unique)
- Business context: table/column comments
- Optional quality metrics: null counts and unique values per column
- Optional lineage: edges derived from foreign key relationships

Built with Strategy + Factory patterns for extensibility.

## Project Structure

```
/atlan-data-source-app/
├── datasource/
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── github/
│   │   ├── __init__.py
│   │   ├── strategy.py
│   │   └── config.example.yaml
│   ├── postgres/
│       ├── __init__.py
│       ├── strategy.py
│       └── config.example.yaml
│   └── redis/
│       ├── __init__.py
│       ├── strategy.py
│       ├── extractors/
│       │   ├── __init__.py
│       │   ├── schema.py
│       │   ├── business.py
│       │   └── quality.py
│       └── config.example.yaml
├── config/
│   └── (optional if using file-based configs)
├── sample_data/
│   └── init.sql
├── main.py
├── requirements.txt
├── README.md
└── THOUGHT_PROCESS.md
```

## Setup

1. Create and activate a virtualenv (Python 3.11+)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Start a local PostgreSQL and load sample data

- Ensure a Postgres server is running locally and accessible.
- Create database and user matching `config/config.yaml`, or update the config to your environment.
- Load sample data:

```bash
psql -h localhost -p 5432 -U sample_user -d sample_db -f sample_data/init.sql
```

3. Configure connection

- Update `config/config.yaml`:

```yaml
type: postgres
host: localhost
port: 5432
database: sample_db
user: sample_user
password: sample_password
```

## Run

- Extract everything:

```bash
python main.py --all
```

- Only schema:

```bash
python main.py --schema
```

- Business context (comments):

```bash
python main.py --business
```

- Quality metrics:

```bash
python main.py --quality
```

- Lineage (foreign key-based):

```bash
python main.py --lineage
```

### GitHub API Source

1. Update `config/config.github.yaml` with your target repository and (optional) token, or set `GITHUB_TOKEN` env var.

```yaml
type: github
owner: octocat
repo: Hello-World
# token: ghp_xxx  # or use env var GITHUB_TOKEN
api_base: https://api.github.com
```

2. Run with GitHub config:

```bash
python main.py --config config/config.github.yaml --all
```

Notes:
- Token is recommended to avoid low unauthenticated rate limits.
- Lineage is based on fork relationships.
- Per-source config examples also live under `datasource/github/config.example.yaml`.

### PostgreSQL Source

- Example config also available at `datasource/postgres/config.example.yaml`.

### Redis Source

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

- **API usage** (`app.py` must be running):

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

## Design

- Strategy Pattern: `datasource/base.py` defines `DataSourceStrategy` interface. `datasource/postgres_strategy.py` implements it for Postgres.
- Factory Pattern: `datasource/factory.py` selects strategy based on `config['type']`.
- Extensibility: Add new sources by creating `your_source_strategy.py` and mapping in the factory.

## Notes

- Quality metric queries can be heavy on large tables. For demo purposes, they run per column; consider sampling / limits in production.
- Comments are used as business context. Add more context systems (tags) if present in your environment.
- Schema extraction includes PK, unique constraints, and FK definitions per table.

## License

For take-home assignment evaluation.
