# FoodSave AI - Konwersacyjny Asystent Zakupowy v1.0

## Opis

**FoodSave AI** to zaawansowany system agentowy, który pozwala na zarządzanie domowym budżetem poprzez konwersacje w języku naturalnym. Zamiast klikać w formularze, możesz po prostu napisać, co chcesz zrobić – dodać nowy paragon, poprawić błąd, usunąć wpis czy zapytać o podsumowanie wydatków – a inteligentny agent przetworzy Twoje polecenie i wykona odpowiednie operacje w bazie danych, prezentując wyniki w formie graficznej.

Projekt ten demonstruje budowę kompletnego, interaktywnego systemu AI od podstaw, łącząc nowoczesny backend, lokalne modele językowe (LLM) oraz zaawansowaną logikę agentową zdolną do prowadzenia dialogu.

## Kluczowe Funkcjonalności

* **Interfejs Graficzny:** Interaktywny czat zbudowany w **Streamlit**.
* **Przetwarzanie Języka Naturalnego (NLU):** Agent rozumie złożone, wielowątkowe polecenia w języku polskim.
* **Pełna Obsługa CRUD+A:**
    * **Create:** Dodawanie paragonów z wieloma produktami i automatyczną kategoryzacją.
    * **Read (Analyze):** Odpowiadanie na pytania analityczne i wizualizacja danych.
    * **Update:** Modyfikacja istniejących wpisów.
    * **Delete:** Usuwanie produktów lub całych paragonów.
* **Obsługa Dialogu i Niejednoznaczności:** Jeśli polecenie jest nieprecyzyjne, agent zadaje pytania doprecyzowujące i rozumie odpowiedzi w kontekście rozmowy.
* **Dynamiczne "Text-to-SQL":** Agent potrafi tłumaczyć pytania analityczne na ustrukturyzowane zapytania do bazy danych z agregacją i filtrowaniem.
* **Modularna Architektura:** System składa się z niezależnych komponentów (UI, API, Baza Danych, Agenci), co ułatwia jego rozwój.
* **Prywatność i Kontrola:** Cała inteligencja opiera się na modelu językowym uruchomionym lokalnie za pomocą Ollama.

## Architektura

System składa się z następujących komponentów:
1. **Frontend (`frontend.py`):** Aplikacja w Streamlit.
2. **Backend (`backend/`):** Aplikacja w FastAPI z logiką agentową.
    * **`orchestrator.py`**: Główny "mózg", który zarządza przepływem.
    * **`tools.py`**: Zestaw narzędzi do interakcji z bazą i generowania odpowiedzi.
    * **`prompts.py`**: Centralny magazyn na prompty systemowe.
    * **`state.py`**: Zarządzanie stanem konwersacji.
    * **`crud.py`**: Niskopoziomowa warstwa dostępu do danych (SQLAlchemy).

## Uruchomienie

1. Przygotuj środowisko i zainstaluj zależności:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Na Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Upewnij się, że serwer Ollama jest uruchomiony z odpowiednim modelem:
   ```bash
   ollama run mistral
   ```

3. Zasil bazę danych:
   ```bash
   python seed_db.py
   ```

4. Uruchom aplikację:
   ```bash
   streamlit run frontend.py
   ```

## Mapa Drogowa

### Kamień Milowy 1: Dalszy Rozwój UI
* Dodanie przycisków do typowych akcji ("Szybkie Akcje")
* Bardziej zaawansowane wykresy (np. kołowe `st.pyplot`)
* Możliwość edycji i usuwania wpisów bezpośrednio z tabeli w UI

### Kamień Milowy 2: Rozszerzenie Inteligencji Agenta
* Wdrożenie pełnej pamięci konwersacyjnej
* Nauczenie agenta obsługi bardziej złożonych filtrów (np. przedziały dat)

### Kamień Milowy 3: Przygotowanie do Produkcji
* Implementacja uwierzytelniania użytkowników
* Konteneryzacja aplikacji (Docker)
* Przejście na produkcyjną bazę danych (PostgreSQL)

## Wymagania Systemowe

* Python 3.8+
* Ollama z modelem Mistral
* SQLite (domyślnie) lub PostgreSQL (opcjonalnie)
* 4GB RAM (minimum)

## Licencja

MIT License - zobacz plik [LICENSE](LICENSE) dla szczegółów.
