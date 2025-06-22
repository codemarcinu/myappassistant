#!/bin/sh

# Install docker-cli
apk add --no-cache docker-cli

# Create log directory
mkdir -p /var/log/ollama

# Follow Ollama logs and add timestamps
docker logs --follow --tail 100 foodsave-ollama-dev 2>&1 |
while read line; do
  echo "$(date '+%Y-%m-%d %H:%M:%S') $line" >> /var/log/ollama/ollama.log;
done
