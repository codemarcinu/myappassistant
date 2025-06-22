#!/usr/bin/env python3
"""
Generate sample chat logs for testing Grafana dashboard
"""

import json
import random
import time
import uuid
from datetime import datetime
import os
from pathlib import Path

# Upewnij się, że katalog logów istnieje
log_dir = Path(__file__).parent.parent / "logs" / "backend"
log_dir.mkdir(parents=True, exist_ok=True)

# Ścieżka do pliku logów
log_file = log_dir / "chat_test.log"

# Przykładowe wiadomości użytkowników
USER_MESSAGES = [
    "Jak mogę zredukować marnowanie żywności?",
    "Podaj przepis na danie z resztek warzyw",
    "Jak długo można przechowywać otwarte mleko?",
    "Co zrobić z czerstwym chlebem?",
    "Jakie produkty najczęściej się marnują?",
    "Jak zaplanować zakupy spożywcze?",
    "Podaj pomysły na wykorzystanie resztek kurczaka",
    "Jak prawidłowo przechowywać owoce?",
    "Jakie są najlepsze metody konserwacji żywności?",
    "Jak długo można przechowywać mrożone mięso?"
]

# Przykładowe odpowiedzi asystenta
ASSISTANT_RESPONSES = [
    "Aby zredukować marnowanie żywności, możesz planować posiłki z wyprzedzeniem, przechowywać żywność prawidłowo i wykorzystywać resztki do nowych potraw.",
    "Z resztek warzyw możesz przygotować pyszną zupę lub zapiekankę. Oto przepis: [przepis]",
    "Otwarte mleko można przechowywać w lodówce do 3-5 dni, zależnie od rodzaju i temperatury lodówki.",
    "Czerstwy chleb świetnie nadaje się na grzanki, bułkę tartą lub pudding chlebowy.",
    "Najczęściej marnowane produkty to pieczywo, owoce i warzywa oraz resztki gotowych posiłków.",
    "Planowanie zakupów powinno zacząć się od inwentaryzacji tego, co już masz, następnie zaplanowania posiłków i stworzenia listy potrzebnych produktów.",
    "Resztki kurczaka można wykorzystać do sałatek, kanapek, zapiekanek lub bulionu.",
    "Większość owoców najlepiej przechowywać w lodówce, z wyjątkiem bananów, cytrusów i awokado, które lepiej trzymać w temperaturze pokojowej.",
    "Najlepsze metody konserwacji to mrożenie, suszenie, kiszenie, pasteryzacja i marynowanie.",
    "Mrożone mięso można przechowywać od 3 do 12 miesięcy, zależnie od rodzaju."
]

# Funkcja generująca pojedynczy log
def generate_chat_log(session_id, is_error=False):
    timestamp = datetime.now().isoformat()
    user_message = random.choice(USER_MESSAGES)
    
    # Losowo wybierz typ zdarzenia
    event_types = ["request_received", "response_completed", "streaming_completed", "error"]
    event_weights = [0.4, 0.3, 0.2, 0.1] if not is_error else [0.1, 0.1, 0.1, 0.7]
    chat_event = random.choices(event_types, weights=event_weights)[0]
    
    # Podstawowe pola logu
    log_data = {
        "timestamp": timestamp,
        "level": "ERROR" if chat_event == "error" else "INFO",
        "logger": "backend.chat",
        "module": "chat",
        "session_id": session_id,
        "chat_event": chat_event
    }
    
    # Dodaj pola specyficzne dla typu zdarzenia
    if chat_event == "request_received":
        log_data["message"] = "Chat request received"
        log_data["message_length"] = len(user_message)
        log_data["use_perplexity"] = random.choice([True, False])
        log_data["use_bielik"] = random.choice([True, False])
        log_data["agent_states"] = {
            "weather": True,
            "search": True,
            "shopping": random.choice([True, False]),
            "cooking": random.choice([True, False])
        }
    
    elif chat_event == "response_completed" or chat_event == "streaming_completed":
        response = random.choice(ASSISTANT_RESPONSES)
        log_data["message"] = f"Chat {'streaming ' if chat_event == 'streaming_completed' else ''}response completed"
        log_data["response_length"] = len(response)
        log_data["success"] = True
        log_data["processing_time_ms"] = random.randint(200, 5000)
        if chat_event == "streaming_completed":
            log_data["chunks_count"] = random.randint(5, 20)
    
    elif chat_event == "error":
        error_types = ["TimeoutError", "ConnectionError", "ValueError", "RuntimeError"]
        error_messages = [
            "Connection to LLM service timed out",
            "Failed to connect to orchestrator",
            "Invalid input format",
            "Unexpected error in processing"
        ]
        error_type = random.choice(error_types)
        error_message = random.choice(error_messages)
        
        log_data["message"] = f"Error in memory_chat_generator: {error_message}"
        log_data["error_type"] = error_type
        log_data["error_message"] = error_message
        log_data["processing_time_ms"] = random.randint(100, 3000)
    
    return json.dumps(log_data)

# Główna funkcja generująca logi
def generate_logs(count=100, interval=0.5):
    # Utwórz kilka sesji
    sessions = [str(uuid.uuid4()) for _ in range(5)]
    
    print(f"Generating {count} chat logs...")
    
    for i in range(count):
        # Wybierz sesję
        session_id = random.choice(sessions)
        
        # Określ czy to będzie log błędu (10% szans)
        is_error = random.random() < 0.1
        
        # Wygeneruj log
        log_entry = generate_chat_log(session_id, is_error)
        
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
    generate_logs(count=100, interval=0.1) 