# FoodSave AI - Konwersacyjny Asystent Zakupowy v1.0

## Opis

FoodSave AI to zaawansowany system agentowy, który pozwala na zarządzanie domowym budżetem poprzez konwersacje w języku naturalnym. Zamiast klikać w formularze, możesz po prostu napisać, co chcesz zrobić – dodać nowy paragon, poprawić błąd, usunąć wpis czy zapytać o podsumowanie wydatków – a inteligentny agent przetworzy Twoje polecenie i wykona odpowiednie operacje w bazie danych, prezentując wyniki w formie graficznej.

Projekt ten demonstruje budowę kompletnego, interaktywnego systemu AI od podstaw, łącząc nowoczesny backend, lokalne modele językowe (LLM) oraz zaawansowaną logikę agentową zdolną do prowadzenia dialogu.

## Kluczowe Funkcjonalności

- **Interfejs Graficzny**: Interaktywny czat zbudowany w Streamlit
- **Przetwarzanie Języka Naturalnego (NLU)**: Agent rozumie złożone, wielowątkowe polecenia w języku polskim
- **Pełna Obsługa CRUD+A**:
  - **Create**: Dodawanie paragonów z wieloma produktami i automatyczną kategoryzacją
  - **Read (Analyze)**: Odpowiadanie na pytania analityczne i wizualizacja danych
  - **Update**: Modyfikacja istniejących wpisów
  - **Delete**: Usuwanie produktów lub całych paragonów
- **Obsługa Dialogu i Niejednoznaczności**: Jeśli polecenie jest nieprecyzyjne, agent zadaje pytania doprecyzowujące i rozumie odpowiedzi w kontekście rozmowy
- **Dynamiczne "Text-to-SQL"**: Agent potrafi tłumaczyć pytania analityczne na ustrukturyzowane zapytania do bazy danych z agregacją i filtrowaniem
- **Modularna Architektura**: System składa się z niezależnych komponentów (UI, API, Baza Danych, Agenci), co ułatwia jego rozwój
- **Prywatność i Kontrola**: Cała inteligencja opiera się na modelu językowym uruchomionym lokalnie za pomocą Ollama

## Architektura

System składa się z następujących komponentów:

### Backend (`backend/`)
- **Agents** - Logika agentowa z orchestratorem, narzędziami i promptami
  - `orchestrator.py`: Główny "mózg", który zarządza przepływem
  - `tools.py`: Zestaw narzędzi do interakcji z bazą i generowania odpowiedzi
  - `prompts.py`: Centralny magazyn na prompty systemowe
  - `state.py`: Zarządzanie stanem konwersacji
- **API** - Interfejs REST API zbudowany na FastAPI
- **Core** - Podstawowe funkcjonalności
  - `crud.py`: Niskopoziomowa warstwa dostępu do danych (SQLAlchemy)
  - `database.py`: Konfiguracja bazy danych
  - `llm_client.py`: Klient Ollama do komunikacji z modelami LLM
  - `ocr.py`: Przetwarzanie obrazów paragonów
- **Models** - Modele danych SQLAlchemy
  - `shopping.py`: Modele ShoppingTrip i Product
- **Schemas** - Schematy Pydantic do walidacji
- **Services** - Warstwa usług biznesowych

### Frontend
- **`frontend_v2.py`** - Główna aplikacja Streamlit z interfejsem użytkownika
- **`frontend/src/`** - Dodatkowe zasoby CSS i stylowanie

### Pozostałe komponenty
- **`tests/`** - Testy jednostkowe, integracyjne i E2E
- **`scripts/`** - Skrypty pomocnicze (setup.sh)
- **`ui/`** - Dodatkowe komponenty interfejsu użytkownika

## Uruchomienie

### 1. Przygotuj środowisko i zainstaluj zależności za pomocą Poetry:

```
# Jeśli nie masz Poetry, zainstaluj globalnie:
pipx install poetry

poetry install

# Aktywuj środowisko Poetry:
poetry shell
```

### 2. Upewnij się, że serwer Ollama jest uruchomiony z odpowiednim modelem:

```
ollama run mistral
```

### 3. Zasil bazę danych:

```
python seed_db.py
```

### 4. Uruchom backend (w osobnym terminalu):

```
cd backend
python -m uvicorn main:app --reload
```

Backend będzie dostępny pod adresem `http://localhost:8000`

### 5. Uruchom frontend (w osobnym terminalu):

```
streamlit run frontend_v2.py
```

Frontend będzie dostępny pod adresem `http://localhost:8501`

## Struktura Bazy Danych

### Tabela `shopping_trips`
- `id` - Unikalny identyfikator wycieczki zakupowej
- `store_name` - Nazwa sklepu
- `date` - Data zakupów
- `total_amount` - Łączna kwota
- `created_at` - Data utworzenia rekordu

### Tabela `products`
- `id` - Unikalny identyfikator produktu
- `shopping_trip_id` - Klucz obcy do tabeli shopping_trips
- `name` - Nazwa produktu
- `price` - Cena produktu
- `quantity` - Ilość
- `category` - Kategoria produktu
- `created_at` - Data utworzenia rekordu

## API Endpoints

### Shopping Trips
- `GET /shopping-trips/` - Pobierz wszystkie wycieczki zakupowe
- `POST /shopping-trips/` - Utwórz nową wycieczkę zakupową
- `GET /shopping-trips/{trip_id}` - Pobierz konkretną wycieczkę
- `PUT /shopping-trips/{trip_id}` - Zaktualizuj wycieczkę
- `DELETE /shopping-trips/{trip_id}` - Usuń wycieczkę

### Products
- `GET /products/` - Pobierz wszystkie produkty
- `POST /products/` - Dodaj nowy produkt
- `GET /products/{product_id}` - Pobierz konkretny produkt
- `PUT /products/{product_id}` - Zaktualizuj produkt
- `DELETE /products/{product_id}` - Usuń produkt

### Agent Conversation
- `POST /chat/` - Endpoint do konwersacji z agentem AI
- `GET /chat/history` - Pobierz historię konwersacji

## Konfiguracja

### Zmienne środowiskowe

Utwórz plik `.env` w głównym katalogu projektu:

```
# Baza danych
DATABASE_URL=sqlite:///./foodsave.db

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral

# API
API_HOST=localhost
API_PORT=8000

# Frontend
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=localhost
```

### Konfiguracja Ollama

```
# Pobierz i uruchom model Mistral
ollama pull mistral
ollama run mistral

# Alternatywnie można użyć других modeli:
ollama pull llama2
ollama pull codellama
```

## Testowanie

### Uruchomienie testów

```
# Wszystkie testy
poetry run pytest

# Testy jednostkowe
poetry run pytest tests/unit/

# Testy integracyjne
poetry run pytest tests/integration/

# Testy E2E
poetry run pytest tests/e2e/

# Testy z pokryciem
poetry run pytest --cov=backend --cov-report=html
```

### Struktura testów

- `tests/unit/` - Testy jednostkowe dla poszczególnych komponentów
- `tests/integration/` - Testy integracji między komponentami
- `tests/e2e/` - Testy end-to-end całego systemu
- `tests/fixtures/` - Dane testowe i fixtury

## Przykłady Użycia

### Dodawanie paragonu przez czat

```
Użytkownik: "Dodaj paragon z Biedronki z wczoraj: mleko 4.50zł, chleb 3.20zł, masło 6.80zł"

Agent: "Dodałem paragon z Biedronki z dnia [wczorajsza data]:
- Mleko: 4,50 zł
- Chleb: 3,20 zł
- Masło: 6,80 zł
Łączna kwota: 14,50 zł"
```

### Analiza wydatków

```
Użytkownik: "Ile wydałem w tym miesiącu na nabiał?"

Agent: "W tym miesiącu wydałeś 67,40 zł na nabiał:
- Mleko: 31,50 zł (7 produktów)
- Masło: 20,40 zł (3 produkty)
- Ser: 15,50 zł (2 produkty)"
```

### Modyfikacja danych

```
Użytkownik: "Zmień cenę mleka z ostatniego paragonu na 4.20zł"

Agent: "Zmieniłem cenę mleka z 4,50 zł na 4,20 zł w paragonie z Biedronki z [data].
Nowa łączna kwota paragonu: 14,20 zł"
```

## Rozwój i Wkład

### Uruchomienie w trybie deweloperskim

```
# Backend z hot reload
cd backend
uvicorn main:app --reload --log-level debug

# Frontend z hot reload
streamlit run frontend_v2.py --server.runOnSave true
```

### Pre-commit hooks

```
# Instalacja pre-commit hooks
poetry run pre-commit install

# Ręczne uruchomienie na wszystkich plikach
poetry run pre-commit run --all-files
```

### Dodawanie nowych funkcjonalności

1. **Nowy agent**: Dodaj logikę w `backend/agents/`
2. **Nowe API endpoint**: Rozszerz `backend/api/`
3. **Nowy model danych**: Dodaj w `backend/models/`
4. **Nowe narzędzie agenta**: Rozszerz `backend/agents/tools.py`
5. **Nowy prompt**: Dodaj w `backend/agents/prompts.py`

## Mapa Drogowa

### Kamień Milowy 1: Dalszy Rozwój UI (W toku)

- ✅ Podstawowy interfejs czatu
- ✅ Wyświetlanie danych produktów
- ❌ Możliwość usuwania wpisów bezpośrednio z tabeli w UI
- ❌ Możliwość edycji wpisów bezpośrednio z tabeli w UI
- ❌ Dodanie przycisków do typowych akcji ("Szybkie Akcje")
- ❌ Bardziej zaawansowane wykresy (np. kołowe `st.pyplot`)

### Kamień Milowy 2: Rozszerzenie Inteligencji Agenta (Priorytet)

- ✅ Podstawowe rozpoznawanie intencji
- ✅ Ekstrakcja encji
- ✅ Zarządzanie stanu konwersacji
- ❌ Wdrożenie pełnej, wieloturowej pamięci konwersacyjnej
- ❌ Nauczenie agenta obsługi złożonych filtrów analitycznych (np. przedziały dat: "w zeszłym tygodniu", "w maju")
- ❌ Ukończenie i przetestowanie wszystkich operacji CRUD w przepływie konwersacyjnym

### Kamień Milowy 3: Przygotowanie do Produkcji

- ❌ Implementacja uwierzytelniania użytkowników
- ✅ Konteneryzacja aplikacji (Docker) - podstawowa
- ❌ Przejście na produkcyjną bazę danych (PostgreSQL)
- ❌ Monitoring i logowanie
- ❌ Testy wydajnościowe

### Kamień Milowy 4: Rozszerzenie Funkcjonalności

- ❌ Integracja z systemami płatności (BLIK, przelewy)
- ❌ Automatyczne kategoryzowanie produktów
- ❌ Generowanie raportów PDF
- ❌ Powiadomienia o przekroczeniu budżetu
- ✅ OCR do przetwarzania paragonów - podstawowa implementacja

### Kamień Milowy 5: Optymalizacja i Skalowanie

- ❌ Optymalizacja zapytań do bazy danych
- ❌ Implementacja cachowania
- ❌ Testy wydajnościowe
- ❌ Monitoring i logowanie
- ❌ Deployment na produkcję

## Rozwiązywanie Problemów

### Częste Problemy

**Problem**: Ollama nie odpowiada
```
# Sprawdź status Ollama
ollama list
ollama ps

# Uruchom ponownie
ollama serve
```

**Problem**: Błąd bazy danych
```
# Usuń i odtwórz bazę
rm foodsave.db
python seed_db.py
```

**Problem**: Frontend nie łączy się z backendem
```
# Sprawdź czy backend działa
curl http://localhost:8000/docs

# Sprawdź porty w .env
```

### Logi

```
# Logi backendu
tail -f backend/logs/app.log

# Logi Streamlit
streamlit run frontend_v2.py --logger.level=debug
```

## Wymagania Systemowe

### Minimalne Wymagania
- **Python**: 3.9+ (z wyłączeniem 3.9.7)
- **RAM**: 4GB (minimum)
- **Dysk**: 2GB wolnego miejsca
- **Procesor**: Dual-core 2.0GHz
- **System**: Windows 10, macOS 10.14, Ubuntu 18.04+

### Zalecane Wymagania
- **Python**: 3.11+
- **RAM**: 8GB
- **Dysk**: 5GB wolnego miejsca (dla modeli LLM)
- **Procesor**: Quad-core 3.0GHz
- **GPU**: Opcjonalnie dla przyspieszenia LLM

### Zależności Systemowe
- **Poetry**: Do zarządzania zależnościami Python
- **Ollama**: Dla lokalnych modeli LLM
- **SQLite**: Domyślna baza danych (wbudowana w Python)
- **Git**: Do klonowania repozytorium

## Zarządzanie Zależnościami

Projekt korzysta z Poetry do zarządzania zależnościami. Zalecane komendy:

```
# Instalacja zależności
poetry install

# Instalacja tylko zależności produkcyjnych
poetry install --no-dev

# Dodawanie nowego pakietu
poetry add NAZWA_PAKIETU

# Dodawanie pakietu deweloperskiego
poetry add --dev NAZWA_PAKIETU

# Aktualizacja zależności
poetry update

# Aktywacja środowiska
poetry shell

# Uruchomienie komendy w środowisku
poetry run python script.py

# Eksport requirements.txt do deployu
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

**Uwaga**: Nie edytuj pliku requirements.txt ręcznie! Jeśli go potrzebujesz, generuj go automatycznie z Poetry.

## Licencja

MIT License - zobacz plik LICENSE dla szczegółów.

## Kontakt i Wsparcie

- **GitHub Issues**: Zgłaszanie błędów i propozycji funkcjonalności
- **Dokumentacja**: Szczegółowa dokumentacja w katalogu `docs/`
- **Wiki**: Dodatkowe przewodniki i tutoriale

## Changelog

### v1.0.0 (Aktualna)
- ✅ Podstawowy system agentowy
- ✅ Interfejs Streamlit
- ✅ Backend FastAPI
- ✅ Integracja z Ollama
- ✅ Podstawowe operacje CRUD
- ✅ OCR dla paragonów

### Planowane w v1.1.0
- Uwierzytelnianie użytkowników
- Ulepszone UI z edycją w tabeli
- Zaawansowana analityka czasowa
- Eksport do PDF

### Planowane w v2.0.0
- Integracja płatności
- Mobilna aplikacja
- Wielojęzyczność
- Synchronizacja w chmurze
```
