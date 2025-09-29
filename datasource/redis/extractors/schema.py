from typing import Any, Dict, Iterable, Tuple

class RedisSchemaExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.scan_count: int = int(config.get("scan_count", 1000))
        self.sample_keys_limit: int = int(config.get("sample_keys_limit", 5000))
        self.include_patterns = config.get("include_patterns") or ["*"]
        self.exclude_patterns = set(config.get("exclude_patterns") or [])

    def _iter_keys(self, r, pattern: str) -> Iterable[str]:
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match=pattern, count=self.scan_count)
            for k in keys:
                yield k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else k
            if cursor == 0:
                break

    def extract(self, r) -> Dict[str, Any]:
        """
        Build a schema-like overview for Redis keyspace:
        - key_samples: up to sample_keys_limit key metadata: {key, type, ttl}
        - type_counts: counts per redis type
        - patterns: optional rollups by top-level prefix (before ':')
        """
        key_samples = []
        type_counts: Dict[str, int] = {}
        prefix_counts: Dict[str, int] = {}

        collected = 0
        for pattern in self.include_patterns:
            for key in self._iter_keys(r, pattern):
                if any(key.startswith(ex) for ex in self.exclude_patterns):
                    continue
                try:
                    ktype = r.type(key)
                    if isinstance(ktype, (bytes, bytearray)):
                        ktype = ktype.decode("utf-8")
                    ttl = r.ttl(key)
                except Exception:
                    # continue on key-level errors
                    continue

                type_counts[ktype] = type_counts.get(ktype, 0) + 1
                prefix = key.split(":", 1)[0] if ":" in key else "__root__"
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1

                if collected < self.sample_keys_limit:
                    key_samples.append({"key": key, "type": ktype, "ttl": ttl})
                    collected += 1
                # do not break early to get accurate type/prefix counts across keyspace

        return {
            "key_samples": key_samples,
            "type_counts": type_counts,
            "prefix_counts": prefix_counts,
        }
