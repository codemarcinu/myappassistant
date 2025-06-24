#!/bin/bash

# Script to start Ollama service and ensure it's running properly
# This script addresses the "Connection refused" error for SpeakLeash/bielik models

set -e

echo "🚀 Starting Ollama service for FoodSave AI..."

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first."
    echo "Visit: https://ollama.ai/download"
    exit 1
fi

# Check if Ollama service is already running
if pgrep -f "ollama serve" > /dev/null; then
    echo "✅ Ollama service is already running"
else
    echo "🔄 Starting Ollama service..."

    # Start Ollama in the background
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!

    # Wait a moment for the service to start
    sleep 3

    # Check if the service started successfully
    if kill -0 $OLLAMA_PID 2>/dev/null; then
        echo "✅ Ollama service started successfully (PID: $OLLAMA_PID)"
    else
        echo "❌ Failed to start Ollama service"
        cat /tmp/ollama.log
        exit 1
    fi
fi

# Wait for Ollama to be ready
echo "⏳ Waiting for Ollama to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        echo "✅ Ollama is ready!"
        break
    fi
    echo "   Attempt $i/30..."
    sleep 2
done

# Check if Ollama is responding
if ! curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
    echo "❌ Ollama is not responding after 60 seconds"
    exit 1
fi

# Pull required models
echo "📥 Pulling required models..."

# Pull Bielik models
echo "   Pulling SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0..."
ollama pull SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0 || echo "⚠️  Failed to pull bielik-4.5b-v3.0-instruct:Q8_0"

echo "   Pulling SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M..."
ollama pull SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M || echo "⚠️  Failed to pull bielik-11b-v2.3-instruct:Q5_K_M"

# Pull Gemma model as fallback
echo "   Pulling gemma3:12b..."
ollama pull gemma3:12b || echo "⚠️  Failed to pull gemma3:12b"

# List available models
echo "📋 Available models:"
ollama list

echo "🎉 Ollama setup completed!"
echo "   Service URL: http://localhost:11434"
echo "   API Version: $(curl -s http://localhost:11434/api/version | jq -r '.version' 2>/dev/null || echo 'unknown')"

# Save PID for later cleanup
echo $OLLAMA_PID > /tmp/ollama.pid
echo "   PID saved to /tmp/ollama.pid"

echo ""
echo "💡 To stop Ollama service:"
echo "   kill \$(cat /tmp/ollama.pid)"
echo ""
echo "💡 To view Ollama logs:"
echo "   tail -f /tmp/ollama.log"
