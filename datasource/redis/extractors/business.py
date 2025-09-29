from typing import Any, Dict, List

class RedisBusinessExtractor:
    def __init__(self, config: Dict[str, Any]):
        # Map key prefixes to human-friendly tags or descriptions
        self.prefix_tags: Dict[str, str] = config.get("prefix_tags", {}) or {}

    def extract(self, r) -> Dict[str, Any]:
        """
        Derive simple business context via configured prefix tags.
        Example: {"user:": "users", "order:": "orders"}
        Returns a mapping of prefix->tag and count of keys per tagged prefix.
        """
        prefix_counts: Dict[str, int] = {}
        for prefix in self.prefix_tags.keys():
            try:
                # Count keys per prefix using SCAN
                count = 0
                cursor = 0
                pattern = f"{prefix}*"
                while True:
                    cursor, keys = r.scan(cursor=cursor, match=pattern, count=1000)
                    count += len(keys)
                    if cursor == 0:
                        break
                prefix_counts[prefix] = count
            except Exception:
                continue
        return {
            "prefix_tags": self.prefix_tags,
            "prefix_counts": prefix_counts,
        }
