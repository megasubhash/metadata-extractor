import logging
import os
import redis

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
logger.info(f"Connecting to Redis at: {redis_url}")

try:
    r = redis.from_url(redis_url)
    r.ping()  # Test connection
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    exit(1)

logger.info("Starting Redis data seeding")

# Strings
logger.info("Creating string keys")
r.set("app:version", "1.0.0")
r.set("order:counter", "1001")
r.set("session:abc123", "token-xyz", ex=3600)

# Hashes
logger.info("Creating hash keys")
r.hset("user:1", mapping={"name": "Subhash", "email": "sahu@example.com", "plan": "free"})
r.hset("user:2", mapping={"name": "Tehjus", "email": "Thejus@atlan.com", "plan": "free"})
r.hset("user:3", mapping={"name": "Atlan", "email": "atlan@atlan.com", "plan": "pro"})
r.hset("order:1001", mapping={"status": "created", "amount": "59.90", "currency": "INR"})
r.hset("order:1002", mapping={"status": "shipped", "amount": "129.00", "currency": "INR"})

# Lists
logger.info("Creating list keys")
r.lpush("queue:emails", "job:1", "job:2", "job:3")

# Sets
logger.info("Creating set keys")
r.sadd("feature:flags", "beta", "ab_test", "dark_mode")

# Sorted set
logger.info("Creating sorted set keys")
r.zadd("leaderboard", {"user:1": 100, "user:2": 250, "user:3": 175})

# TTL examples
logger.info("Creating keys with TTL")
r.set("session:u1", "sess-token-u1", ex=1200)
r.set("session:u2", "sess-token-u2", ex=900)

logger.info("Redis data seeding completed successfully")
print("Seeded Redis sample data.")