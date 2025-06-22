#!/usr/bin/env python3
"""
Generate sample frontend logs for testing Grafana dashboard
"""

import random
import time
import uuid
from datetime import datetime
import os
from pathlib import Path

# Upewnij się, że katalog logów istnieje
log_dir = Path(__file__).parent.parent / "logs" / "frontend"
log_dir.mkdir(parents=True, exist_ok=True)

# Ścieżka do pliku logów
log_file = log_dir / "test.log"

# Przykładowe zdarzenia interfejsu czatu
CHAT_EVENTS = [
    "Chat interface initialized",
    "Chat component mounted in UI",
    "Chat message sent to API",
    "Chat message received from API",
    "Chat message displayed in UI",
    "Chat error: Failed to connect to API",
    "Chat streaming response started",
    "Chat streaming response chunk received",
    "Chat streaming response completed",
    "Chat message history loaded",
    "Chat session created with ID: {}",
    "Chat UI state updated",
    "Chat input focus changed",
    "Chat message {} characters typed",
    "Chat send button clicked",
    "Chat message {} sent to backend",
    "Chat response rendering started",
    "Chat response rendering completed in {}ms",
    "Chat component unmounted"
]

# Funkcja generująca pojedynczy log
def generate_frontend_log(is_error=False):
    timestamp = datetime.now()
    timestamp_str = timestamp.strftime("%a, %d %b %Y, %H:%M:%S %Z")
    
    # Wybierz zdarzenie
    if is_error:
        event = "Chat error: " + random.choice([
            "Failed to connect to API",
            "Timeout waiting for response",
            "Invalid response format",
            "WebSocket connection closed",
            "Failed to parse message"
        ])
        level = "ERROR"
    else:
        event_template = random.choice(CHAT_EVENTS)
        if "{}" in event_template:
            if "ms" in event_template:
                event = event_template.format(random.randint(50, 500))
            elif "characters" in event_template:
                event = event_template.format(random.randint(10, 200))
            elif "ID" in event_template:
                event = event_template.format(str(uuid.uuid4())[:8])
            else:
                event = event_template.format(random.choice(["Hello", "How are you?", "Tell me about food waste", "What can I cook with leftover vegetables?"]))
        else:
            event = event_template
        level = "INFO"
    
    return f"[{timestamp_str}] {level}: {event}"

# Główna funkcja generująca logi
def generate_logs(count=50, interval=0.2):
    print(f"Generating {count} frontend chat logs...")
    
    for i in range(count):
        # Określ czy to będzie log błędu (10% szans)
        is_error = random.random() < 0.1
        
        # Wygeneruj log
        log_entry = generate_frontend_log(is_error)
        
        # Zapisz do pliku
        with open(log_file, "a") as f:
            f.write(log_entry + "\n")
        
        print(f"Generated log {i+1}/{count}", end="\r")
        
        # Poczekaj chwilę
        time.sleep(interval)
    
    print(f"\nDone! Logs saved to {log_file}")

if __name__ == "__main__":
    # Wyczyść plik logów jeśli istnieje
    if log_file.exists():
        os.remove(log_file)
    
    # Wygeneruj logi
    generate_logs(count=50, interval=0.1) 