# FoodSave AI - Asystent Zakupowy

FoodSave AI to inteligentny asystent zakupowy, który pomaga w śledzeniu i analizie wydatków na żywność. Aplikacja wykorzystuje naturalny język do komunikacji z użytkownikiem, umożliwiając łatwe dodawanie paragonów i analizę wydatków.

## Funkcjonalności

- Dodawanie paragonów poprzez naturalną konwersację
- Analiza wydatków według kategorii i sklepów
- Wizualizacja danych w formie wykresów
- Inteligentne wyszukiwanie i filtrowanie danych
- Obsługa polskich nazw miesięcy i dat

## Wymagania

- Python 3.8+
- Streamlit
- SQLAlchemy
- Inne zależności wymienione w `requirements.txt`

## Instalacja

1. Sklonuj repozytorium:
```bash
git clone https://github.com/twoj-username/foodsave-ai.git
cd foodsave-ai
```

2. Utwórz i aktywuj środowisko wirtualne:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# lub
venv\Scripts\activate  # Windows
```

3. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

## Uruchomienie

Aby uruchomić aplikację, wykonaj:
```bash
streamlit run frontend.py
```

Aplikacja będzie dostępna pod adresem: http://localhost:8501

## Przykłady użycia

1. Dodawanie paragonu:
```
Dodaj paragon z Biedronki z dzisiaj:
- Mleko 2%, 2 sztuki po 3.99 zł
- Chleb razowy, 1 sztuka po 4.50 zł
```

2. Analiza wydatków:
```
Pokaż podsumowanie wydatków według kategorii
Pokaż wydatki w tym miesiącu
```

## Struktura projektu

```
foodsave-ai/
├── backend/
│   ├── agents/
│   ├── core/
│   └── models/
├── frontend.py
├── requirements.txt
└── README.md
```

## Licencja

MIT

## Autor

[Twoje Imię i Nazwisko]
