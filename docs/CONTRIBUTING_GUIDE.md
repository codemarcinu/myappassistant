# Przewodnik dla współtwórców projektu FoodSave AI

## Wprowadzenie

Dziękujemy za zainteresowanie projektem FoodSave AI! Ten dokument zawiera wskazówki dotyczące procesu rozwoju, standardów kodowania i procedur współpracy. Przestrzeganie tych wytycznych pomoże utrzymać wysoką jakość kodu i ułatwi współpracę.

## Struktura projektu

Projekt FoodSave AI składa się z dwóch głównych części:

1. **Backend (FastAPI)** - Znajduje się w katalogu `src/backend`
2. **Frontend (Next.js)** - Znajduje się w katalogu `foodsave-frontend`

## Przygotowanie środowiska deweloperskiego

### Wymagania wstępne

- Python 3.10+
- Node.js 18+
- Docker i Docker Compose
- Poetry (zarządzanie zależnościami Python)
- npm lub yarn (zarządzanie zależnościami JavaScript)

### Konfiguracja środowiska

1. Sklonuj repozytorium:
   ```bash
   git clone https://github.com/yourusername/foodsave-ai.git
   cd foodsave-ai
   ```

2. Skonfiguruj backend:
   ```bash
   cd src/backend
   poetry install
   ```

3. Skonfiguruj frontend:
   ```bash
   cd foodsave-frontend
   npm install
   ```

4. Uruchom środowisko deweloperskie:
   ```bash
   docker-compose -f docker-compose.dev.yaml up
   ```

## Konwencje kodowania

### Python (Backend)

- Używaj **PEP 8** jako podstawowego stylu kodowania
- Maksymalna długość linii: 88 znaków (zgodnie z Black)
- Używaj typowania statycznego (type hints)
- Dokumentuj klasy i funkcje za pomocą docstringów w formacie Google
- Używaj pytest do testów

### TypeScript/JavaScript (Frontend)

- Używaj ESLint i Prettier do formatowania kodu
- Używaj TypeScript zamiast JavaScript, gdy to możliwe
- Preferuj komponenty funkcyjne i hooki React
- Używaj testów jednostkowych z Jest i React Testing Library

### Konwencje importów

- W kodzie backendu używaj bezpośrednich importów z modułu `backend` zamiast `src.backend`
  ```python
  # Prawidłowo
  from backend.agents.tools import ShoppingTool

  # Nieprawidłowo
  from src.backend.agents.tools import ShoppingTool
  ```

- Importy powinny być pogrupowane w następującej kolejności:
  1. Importy standardowej biblioteki Python
  2. Importy zewnętrznych bibliotek
  3. Importy z projektu FoodSave AI
  4. Importy lokalne z bieżącego modułu

- Używaj importów bezwzględnych zamiast względnych, gdy to możliwe

- Unikaj importów cyklicznych

- Sprawdzaj poprawność importów za pomocą narzędzi takich jak isort i mypy

## Proces rozwoju

### Gałęzie i przepływ pracy

- `main` - główna gałąź produkcyjna
- `develop` - gałąź rozwojowa
- `feature/*` - gałęzie funkcji
- `bugfix/*` - gałęzie naprawy błędów
- `release/*` - gałęzie wydań

### Proces Pull Request

1. Utwórz nową gałąź z `develop` dla swojej funkcji lub poprawki
2. Wprowadź zmiany i przetestuj je lokalnie
3. Wypchnij zmiany do swojej gałęzi
4. Utwórz pull request do gałęzi `develop`
5. Poczekaj na przegląd kodu i testy CI
6. Po zatwierdzeniu, twoje zmiany zostaną scalone

### Standardy commit

Używaj konwencji Conventional Commits:

```
<typ>(<zakres>): <opis>

[opcjonalne ciało]

[opcjonalne stopki]
```

Gdzie `<typ>` to jeden z:
- `feat`: nowa funkcja
- `fix`: naprawa błędu
- `docs`: zmiany w dokumentacji
- `style`: formatowanie, brakujące średniki itp.
- `refactor`: refaktoryzacja kodu
- `test`: dodawanie testów
- `chore`: aktualizacje zadań budowania, konfiguracji itp.

## Testowanie

### Backend

- Wszystkie nowe funkcje powinny mieć testy jednostkowe
- Uruchom testy za pomocą `pytest`
- Sprawdź pokrycie kodu za pomocą `pytest --cov=backend`

### Frontend

- Testuj komponenty za pomocą Jest i React Testing Library
- Uruchom testy za pomocą `npm test`
- Dodaj testy e2e za pomocą Playwright dla krytycznych ścieżek

## Dokumentacja

- Aktualizuj dokumentację API, gdy zmieniasz endpointy
- Aktualizuj dokumentację użytkownika, gdy zmieniasz funkcje widoczne dla użytkownika
- Dokumentuj złożone algorytmy i decyzje projektowe

## Zgłaszanie problemów

- Użyj szablonów problemów do zgłaszania błędów lub propozycji funkcji
- Podaj jak najwięcej szczegółów, w tym kroki do odtworzenia, oczekiwane i rzeczywiste zachowanie
- Dołącz zrzuty ekranu lub logi, jeśli to możliwe

## Kontakt

Jeśli masz pytania, które nie są objęte tym przewodnikiem, skontaktuj się z zespołem FoodSave AI:

- Email: team@foodsave.ai
- Slack: #foodsave-development

Dziękujemy za Twój wkład w projekt FoodSave AI!
