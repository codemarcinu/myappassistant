#!/bin/sh

# Install docker-cli
apk add --no-cache docker-cli

# Create log directory
mkdir -p /var/log/ollama

# Get the container ID of the Ollama container (handle both possible names)
OLLAMA_CONTAINER=$(docker ps | grep -E 'foodsave-ollama-dev|.*_foodsave-ollama-dev' | awk '{print $1}')

if [ -z "$OLLAMA_CONTAINER" ]; then
  echo "$(date '+%Y-%m-%d %H:%M:%S') Error: Ollama container not found" >> /var/log/ollama/ollama.log
  echo "Waiting for Ollama container to start..."
  sleep 10
  exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') Found Ollama container: $OLLAMA_CONTAINER" >> /var/log/ollama/ollama.log

# Follow Ollama logs and add timestamps
docker logs --follow --tail 100 $OLLAMA_CONTAINER 2>&1 |
while read line; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') $line" >> /var/log/ollama/ollama.log;
done
