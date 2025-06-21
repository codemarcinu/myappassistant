#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### Starting Development Environment ###"

# Create logs directory if it doesn't exist
mkdir -p logs/backend
mkdir -p logs/frontend

# 1. Backend Setup
echo "--- Setting up backend ---"
(
  # No need to cd, poetry runs from project root
  echo "Installing Python dependencies with Poetry..."
  poetry install
  echo "Backend dependencies installed."
)

# 2. Frontend Setup
echo "--- Setting up frontend ---"
(
  cd foodsave-frontend
  echo "Installing Node.js dependencies..."
  npm install
  echo "Frontend dependencies installed."
)

# 3. Environment variables
echo "--- Setting up environment variables ---"
if [ ! -f .env ]; then
  echo "Creating .env file from .env.example..."
  cp env.dev.example .env
else
  echo ".env file already exists."
fi

echo "--- Starting services in tmux ---"

SESSION="foodsave-dev"
tmux start-server

# Kill session if it exists to ensure a clean start
tmux kill-session -t $SESSION || true

# Create a new session with a 2x2 layout
tmux new-session -d -s $SESSION
tmux split-window -h
tmux split-window -v -t 0
tmux select-pane -t 1
tmux split-window -v
tmux select-layout tiled

# Pane 0 (top-left): Backend
tmux send-keys -t $SESSION:0.0 "echo '--- Starting Backend ---'; poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --app-dir ./src &> logs/backend/server.log" C-m

# Pane 1 (top-right): Frontend
tmux send-keys -t $SESSION:0.1 "echo '--- Starting Frontend ---'; cd foodsave-frontend && npm run dev -- -p 3000 &> ../logs/frontend/server.log" C-m

# Pane 2 (bottom-left): Ollama
tmux send-keys -t $SESSION:0.2 "echo '--- Starting Ollama ---'; ollama serve" C-m

# Pane 3 (bottom-right): Log viewer with gotty
tmux send-keys -t $SESSION:0.3 "echo '--- Starting Log Viewer ---'; echo 'Waiting for log files...'; sleep 3; gotty --title-format 'FoodSave AI Logs' tail -f logs/backend/server.log logs/frontend/server.log" C-m


echo "### Development Environment Started in tmux session '$SESSION' ###"
echo "To attach to the session, run: tmux attach -t $SESSION"
echo "To kill the session, run: tmux kill-session -t $SESSION"
echo "Real-time logs available in your browser at: http://localhost:8080"
