# Thought Process & Design Decisions

## Source Choice
- **GitHub** chosen to showcase a modern API source. It provides rich metadata (repo info, issues, PRs, topics) and a natural graph (fork lineage). See `datasource/github/`.
- **Redis** chosen to demonstrate a schemaless KV store. It exercises keyspace scanning, TTL posture, and naming conventions for business context. See `datasource/redis/`.

## Patterns & Architecture
- **Strategy Pattern** to support pluggable sources. `datasource/base.py` defines `DataSourceStrategy` with `extract_schema()`, `extract_business_context()`, `extract_lineage()`, `extract_quality_metrics()`.
- **Factory Pattern** to construct the right strategy from `config['type']`. See `datasource/factory.py`.
- **Per-extractor composition** for separation of concerns: each strategy delegates to `extractors/` modules per concern (schema, business, lineage, quality). Examples:
  - GitHub: `datasource/github/extractors/{schema,business,lineage,quality}.py` via `datasource/github/strategy.py`.
  - Redis: `datasource/redis/extractors/{schema,business,quality}.py` via `datasource/redis/strategy.py`.
- **API-first runtime** with Flask: `app.py` exposes `POST /extract` taking inline config and flags, plus optional OpenMetadata publish.
- **Optional publisher**: `integrations/openmetadata_adapter.py` maps extracted outputs to OpenMetadata entities. Kept optional to keep core self-contained.

## Metadata Scope & Rationale
- **Schema**
  - GitHub: field lists defining logical entities (`repository`, `issue`, `pull_request`) in `datasource/github/extractors/schema.py` — sets contract for downstream use.
  - Redis: `key_samples`, `type_counts`, `prefix_counts` in `datasource/redis/extractors/schema.py` — practical structure for schemaless stores.
- **Business Context**
  - GitHub: `description`, `homepage`, `default_branch`, `license`, `topics` from repo (`datasource/github/extractors/business.py`).
  - Redis: `prefix_tags` mapping (config) and per-prefix counts (`datasource/redis/extractors/business.py`).
- **Lineage**
  - GitHub: fork graph (parent → fork, and outgoing forks) in `datasource/github/extractors/lineage.py`.
  - Redis: N/A (returns empty `{ "edges": [] }`).
- **Quality Metrics**
  - GitHub: popularity and health proxies (stars/forks/watchers, issue/PR counts, avg issue close time) in `datasource/github/extractors/quality.py`.
  - Redis: `total_keys`, TTL posture, sampled type counts in `datasource/redis/extractors/quality.py`.

## Libraries & Tools
- **requests** for GitHub REST (`datasource/github/strategy.py`).
- **redis-py** for Redis (`datasource/redis/strategy.py`).
- **Flask** for API (`app.py`).
- (Optional) **OpenMetadata client** for publishing (`integrations/openmetadata_adapter.py`).

## Tradeoffs Considered
- **Simplicity vs completeness**: Chose high-signal fields and light metrics; deferred pagination (GitHub) and heavy profiling (Redis value sampling) to keep demo snappy.
- **Self-contained vs integrations**: OpenMetadata is optional so the core app runs locally with zero proprietary dependencies.
- **Performance vs fidelity**: Redis SCAN bounded by `scan_count`/`sample_keys_limit`; GitHub stats based on limited pages to respect rate limits.
- **Uniform interface vs source nuances**: Unified extractor API while tailoring what “schema/lineage/quality” means per source.

## Core vs Optional Requirements
- **Core**: Schema + business context per source; `/extract` API in `app.py`; docs and sample data.
- **Optional**: Lineage and quality metrics; OpenMetadata publishing.

## Production Considerations
- **Error handling**: Per-key try/except (Redis); centralized HTTP `_get()` (GitHub). API returns `400` with `{error: ...}`.
- **Scalability**: Redis SCAN for non-blocking iteration; plan pagination/backoff for GitHub.
- **Security**: Use env for tokens (e.g., `GITHUB_TOKEN`); avoid logging secrets; allow config files for local runs.
- **Extensibility**: Add `datasource/<source>/strategy.py` + `extractors/`, map in `datasource/factory.py`, automatically available via API.

## Future Work
- GitHub: pagination, retry/backoff, timeouts.
- Redis: per-type value sampling; optional Memory USAGE with fallbacks.
- API: request validation (pydantic), auth, structured logging, output schema validation.
- Publishing: robust type mapping, idempotent upserts, batching.
