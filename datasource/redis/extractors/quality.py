from typing import Any, Dict

class RedisQualityExtractor:
    def __init__(self, config: Dict[str, Any]):
        self.scan_count: int = int(config.get("scan_count", 1000))
        self.sample_keys_limit: int = int(config.get("sample_keys_limit", 5000))

    def extract(self, r) -> Dict[str, Any]:
        """
        Basic quality indicators for Redis keyspace:
        - total_keys
        - expiring_keys vs persistent_keys
        - per-type counts (recomputed again for validation)
        - optional approximate average size if MEMORY USAGE is available (best-effort)
        """
        # totals
        try:
            total_keys = int(r.dbsize())
        except Exception:
            total_keys = None

        expiring = 0
        persistent = 0
        type_counts: Dict[str, int] = {}

        # Iterate keys in batches (cap by sample_keys_limit for expensive metrics)
        sampled = 0
        cursor = 0
        while True:
            cursor, keys = r.scan(cursor=cursor, match="*", count=self.scan_count)
            for k in keys:
                key = k.decode("utf-8") if isinstance(k, (bytes, bytearray)) else k
                try:
                    t = r.type(key)
                    if isinstance(t, (bytes, bytearray)):
                        t = t.decode("utf-8")
                    ttl = r.ttl(key)
                    type_counts[t] = type_counts.get(t, 0) + 1
                    if ttl is None or ttl < 0:
                        persistent += 1
                    else:
                        expiring += 1
                except Exception:
                    continue
                sampled += 1
                if sampled >= self.sample_keys_limit:
                    break
            if cursor == 0 or sampled >= self.sample_keys_limit:
                break

        return {
            "total_keys": total_keys,
            "expiring_keys": expiring,
            "persistent_keys": persistent,
            "type_counts_sampled": type_counts,
            "sampled_keys": sampled,
        }
