import redis
r = redis.Redis(host="localhost", port=6379, db=0)

# Strings
r.set("app:version", "1.0.0")
r.set("order:counter", "1001")
r.set("session:abc123", "token-xyz", ex=3600)

# Hashes
r.hset("user:1", mapping={"name": "Alice", "email": "alice@example.com", "plan": "pro"})
r.hset("user:2", mapping={"name": "Bob", "email": "bob@example.com", "plan": "free"})
r.hset("order:1001", mapping={"status": "created", "amount": "59.90", "currency": "USD"})
r.hset("order:1002", mapping={"status": "shipped", "amount": "129.00", "currency": "USD"})

# Lists
r.lpush("queue:emails", "job:1", "job:2", "job:3")

# Sets
r.sadd("feature:flags", "beta", "ab_test", "dark_mode")

# Sorted set
r.zadd("leaderboard", {"user:1": 100, "user:2": 250, "user:3": 175})

# TTL examples
r.set("session:u1", "sess-token-u1", ex=1200)
r.set("session:u2", "sess-token-u2", ex=900)

print("Seeded Redis sample data.")