#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME=${CONTAINER_NAME:-local-redis}
IMAGE_TAG=${IMAGE_TAG:-redis:7}
HOST_PORT=${HOST_PORT:-6379}
CONTAINER_PORT=${CONTAINER_PORT:-6379}

# Check docker availability
if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is not installed or not in PATH. Please install Docker Desktop and retry." >&2
  exit 1
fi

# Check if host port is available (unless the container is already running and bound to it)
port_in_use() {
  if command -v lsof >/dev/null 2>&1; then
    lsof -i TCP:${HOST_PORT} -sTCP:LISTEN >/dev/null 2>&1
    return $?
  elif command -v netstat >/dev/null 2>&1; then
    netstat -an | grep -E "\.${HOST_PORT} .*LISTEN" >/dev/null 2>&1
    return $?
  else
    # Best-effort: assume free if we can't check
    return 1
  fi
}

# If container exists and is running
if docker ps --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  echo "Redis container '${CONTAINER_NAME}' is already running."
  exit 0
fi

# If container exists but stopped, start it
if docker ps -a --filter "name=^/${CONTAINER_NAME}$" --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  if port_in_use; then
    echo "ERROR: Host port ${HOST_PORT} is already in use. Stop the process using it or set HOST_PORT to a free port." >&2
    exit 1
  fi
  echo "Starting existing Redis container '${CONTAINER_NAME}'..."
  docker start "${CONTAINER_NAME}"
else
  if port_in_use; then
    echo "ERROR: Host port ${HOST_PORT} is already in use. Stop the process using it or set HOST_PORT to a free port." >&2
    exit 1
  fi
  echo "Launching new Redis container '${CONTAINER_NAME}' from image ${IMAGE_TAG}..."
  docker run -d \
    --name "${CONTAINER_NAME}" \
    -p "${HOST_PORT}:${CONTAINER_PORT}" \
    "${IMAGE_TAG}"
fi

# Wait for readiness (ping)
ATTEMPTS=20
SLEEP_SECS=1
for i in $(seq 1 ${ATTEMPTS}); do
  if docker exec "${CONTAINER_NAME}" redis-cli ping >/dev/null 2>&1; then
    echo "Redis is up and responding (container: ${CONTAINER_NAME}, port ${HOST_PORT})."
    exit 0
  fi
  echo "Waiting for Redis to be ready... (${i}/${ATTEMPTS})"
  sleep ${SLEEP_SECS}
done

echo "WARNING: Redis container started but did not respond to PING in time. It may still be initializing." >&2
exit 0
