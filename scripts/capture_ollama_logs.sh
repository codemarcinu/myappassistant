#!/bin/bash

# Script to capture Ollama logs and write them to a file
# This allows Promtail to read Ollama logs from a file

LOG_DIR="/var/log/ollama"
LOG_FILE="$LOG_DIR/ollama.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function to handle cleanup
cleanup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Stopping Ollama log capture" >> "$LOG_FILE"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Start Ollama and capture all output
echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] Starting Ollama log capture" >> "$LOG_FILE"

# Run ollama serve and capture all output
exec ollama serve 2>&1 | while IFS= read -r line; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') $line" >> "$LOG_FILE"
done
