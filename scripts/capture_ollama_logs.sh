#!/bin/bash

# Script to capture Ollama logs for monitoring
# Author: FoodSave AI Team
# Date: 2024

LOG_DIR="logs/ollama"
LOG_FILE="${LOG_DIR}/ollama_$(date +%Y%m%d_%H%M%S).log"

# Ensure log directory exists
mkdir -p ${LOG_DIR}

echo "Starting Ollama log capture to ${LOG_FILE}"
echo "Press Ctrl+C to stop logging"

# Log Ollama container output
docker logs -f foodsave-ollama 2>&1 | tee -a ${LOG_FILE} &
DOCKER_PID=$!

# Add timestamp to logs
while read -r line; do
  echo "$(date +'%Y/%m/%d %H:%M:%S') INFO $line" >> ${LOG_FILE}
done

# Handle Ctrl+C gracefully
trap "kill $DOCKER_PID; echo 'Stopping log capture'; exit 0" SIGINT SIGTERM

# Wait indefinitely
wait $DOCKER_PID
