# Thought Process & Design Decisions

## Source Choice
- **PostgreSQL** chosen for richness of metadata (information_schema, comments), easy local setup, and realistic enterprise usage.

## Patterns
- **Strategy Pattern** to support pluggable data sources. `DataSourceStrategy` defines the interface, `PostgresStrategy` implements.
- **Factory Pattern** to construct the appropriate strategy based on `config['type']`.

## Metadata Scope
- **Schema**: tables and columns with data types, nullability, defaults.
- **Business Context**: comments on tables/columns.
- **Quality Metrics (optional)**: per-column null counts and unique counts. Heavy on big tables; suitable for demo. In prod: sampling, limits, column profiling frameworks.

## Extensibility
- Add a new data source by implementing a new `XStrategy` class inheriting from `DataSourceStrategy` and mapping in `DataSourceFactory`.
- Config-driven type selection enables swapping sources without code changes.

## Trade-offs
- **psycopg2** for simplicity; an ORM (SQLAlchemy) could simplify portability but adds overhead.
- Direct SQL for maximum control and transparency.
- Quality metrics computed via full scans; acceptable for sample data, but consider:
  - Sampling
  - HyperLogLog/approx distinct
  - LIMIT per table/column

## Production Considerations
- **Security**: Use env vars or secrets manager. Avoid committing credentials. Support SSL params.
- **Rate limiting**: Not applicable for Postgres, but for APIs add backoff/retries.
- **Change detection**: Track last extracted timestamps; only profile changed tables/columns.
- **Error handling**: Wrap DB ops with try/except, return structured errors. Fail per-table, continue others.
- **Recovery**: Idempotent extraction; checkpoint progress; resume.
- **Monitoring**: Log metrics and extraction stats; expose Prometheus counters.
- **Configuration**: YAML + env var overrides; per-environment files.

## Future Work
- Add lineage extraction (FKs) and graph output (e.g., NetworkX, DOT).
- Add constraints (PK, FK, unique) to schema output.
- Output to JSONL/CSV and write to a target (files, API).
- Add additional sources: MySQL, SQLite (for zero-setup demo), GitHub API.
- CLI improvements: include/exclude tables, limit rows for profiling.
