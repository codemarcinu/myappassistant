# RAG System Guide - FoodSave AI

## Przegląd

System RAG (Retrieval-Augmented Generation) w aplikacji FoodSave AI umożliwia wzbogacanie odpowiedzi AI o wiedzę z dokumentów, historii zakupów, stanu spiżarni i rozmów. System automatycznie przetwarza dokumenty, generuje embeddings i umożliwia semantyczne wyszukiwanie.

## Architektura Systemu

### Komponenty

1. **RAG Document Processor** (`src/backend/core/rag_document_processor.py`)
   - Przetwarzanie dokumentów (PDF, DOCX, TXT, MD, HTML)
   - Chunking tekstu z nakładaniem się
   - Generowanie embeddings
   - Integracja z vector store

2. **RAG Integration** (`src/backend/core/rag_integration.py`)
   - Synchronizacja bazy danych z RAG
   - Konwersja rekordów na dokumenty
   - Automatyczne aktualizacje

3. **Vector Store** (`src/backend/core/vector_store.py`)
   - Przechowywanie embeddings
   - Semantyczne wyszukiwanie
   - Zarządzanie metadanymi

4. **API Endpoints** (`src/backend/api/v2/endpoints/rag.py`)
   - Upload dokumentów
   - Synchronizacja bazy danych
   - Wyszukiwanie
   - Statystyki systemu

## Jak Dodać Dokumenty

### 1. Przez Interfejs Webowy

Przejdź do `/rag` w aplikacji i użyj formularza upload:

```typescript
// Przykład użycia komponentu RAGManager
<RAGManager />
```

### 2. Przez API

```bash
# Upload dokumentu
curl -X POST "http://localhost:8000/api/v2/rag/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf" \
  -F "category=recipes" \
  -F "tags=cooking,healthy,quick"
```

### 3. Przez CLI

```bash
# Dodaj pojedynczy plik
python scripts/rag_cli.py add-file data/docs/recipe.pdf --tags="cooking,healthy"

# Dodaj katalog
python scripts/rag_cli.py add-directory data/docs --recursive --extensions=".pdf,.docx,.txt"

# Dodaj z URL
python scripts/rag_cli.py add-url https://example.com/recipe-guide
```

### 4. Programowo w Pythonie

```python
from src.backend.core.rag_document_processor import rag_document_processor

# Przetwórz dokument
result = await rag_document_processor.process_file(
    "path/to/document.pdf",
    metadata={"category": "recipes", "tags": ["cooking", "healthy"]}
)

# Przetwórz tekst
chunks = await rag_document_processor.process_document(
    content="Treść dokumentu...",
    source_id="my_document",
    metadata={"type": "recipe", "author": "Chef AI"}
)
```

## Integracja z Bazą Danych

### Automatyczna Synchronizacja

System automatycznie konwertuje dane z bazy na dokumenty RAG:

#### Paragony (Receipts)
```python
# Format automatycznie generowany
"""
Paragon z Biedronka z dnia 2024-01-15

Produkty:
- Chleb: 1 szt. @ 3.50 zł
- Masło: 1 szt. @ 6.99 zł
- Ser żółty: 1 szt. @ 12.99 zł

Suma: 23.48 zł
"""
```

#### Spiżarnia (Pantry)
```python
# Format automatycznie generowany
"""
Stan spiżarni - ostatnia aktualizacja: 2024-01-15 14:30

Dostępne produkty:
- Mleko: 2 szt. (wygasa: 2024-01-20)
- Chleb: 1 szt. (wygasa: 2024-01-17)
- Masło: 1 szt. (wygasa: 2024-01-25)

Łącznie: 4 produkty
"""
```

#### Rozmowy (Conversations)
```python
# Format automatycznie generowany
"""
Rozmowa z 2024-01-15 14:30

Pytanie: Jakie przepisy mogę przygotować z dostępnych składników?
Odpowiedź: Na podstawie Twojej spiżarni mogę zaproponować...

Typ: cooking_assistant
"""
```

### Synchronizacja przez API

```bash
# Synchronizuj paragony
curl -X POST "http://localhost:8000/api/v2/rag/sync-database?sync_type=receipts"

# Synchronizuj spiżarnię
curl -X POST "http://localhost:8000/api/v2/rag/sync-database?sync_type=pantry"

# Synchronizuj rozmowy
curl -X POST "http://localhost:8000/api/v2/rag/sync-database?sync_type=conversations"

# Synchronizuj wszystko
curl -X POST "http://localhost:8000/api/v2/rag/sync-database?sync_type=all"
```

## Wyszukiwanie i Użycie

### Wyszukiwanie przez API

```bash
# Podstawowe wyszukiwanie
curl "http://localhost:8000/api/v2/rag/search?query=przepisy z kurczakiem&k=5"

# Wyszukiwanie z filtrami
curl "http://localhost:8000/api/v2/rag/search?query=zdrowe jedzenie&filter_type=recipe&min_similarity=0.7"
```

### Programowe Wyszukiwanie

```python
from src.backend.core.vector_store import vector_store

# Wyszukaj dokumenty
results = await vector_store.search(
    query="przepisy z kurczakiem",
    k=5,
    filter_metadata={"type": "recipe"},
    min_similarity=0.65
)

for result in results:
    print(f"Similarity: {result['similarity']:.3f}")
    print(f"Text: {result['text']}")
    print(f"Source: {result['source_id']}")
    print(f"Metadata: {result['metadata']}")
```

### Integracja z Agentami

```python
from src.backend.agents.rag_agent import RAGAgent

# Utwórz agenta RAG
rag_agent = RAGAgent("cooking-assistant")

# Wyszukaj kontekst
context = await rag_agent.search("przepisy z dostępnych składników")

# Użyj kontekstu w odpowiedzi
response = await rag_agent.generate_response(
    query="Co mogę ugotować?",
    context=context
)
```

## Konfiguracja

### Zmienne Środowiskowe

```bash
# Konfiguracja embeddings
USE_LOCAL_EMBEDDINGS=true
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Konfiguracja Pinecone (opcjonalnie)
PINECONE_API_KEY=your-api-key
PINECONE_INDEX=your-index-name
USE_PINECONE=false

# Konfiguracja chunking
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
```

### Konfiguracja w Kodzie

```python
from src.backend.core.rag_document_processor import RAGDocumentProcessor

# Utwórz processor z niestandardowymi ustawieniami
processor = RAGDocumentProcessor(
    chunk_size=1500,  # Większe chunki
    chunk_overlap=300,  # Większe nakładanie
    use_local_embeddings=True,  # Użyj lokalnych embeddings
    use_pinecone=False  # Użyj lokalnego vector store
)
```

## Monitorowanie i Statystyki

### Statystyki Systemu

```bash
# Pobierz statystyki
curl "http://localhost:8000/api/v2/rag/stats"
```

Odpowiedź:
```json
{
  "status_code": 200,
  "message": "Statistics retrieved successfully",
  "data": {
    "vector_store": {
      "total_chunks": 1250,
      "total_documents": 45
    },
    "processor": {
      "chunk_size": 1000,
      "chunk_overlap": 200,
      "use_local_embeddings": true,
      "use_pinecone": false
    }
  }
}
```

### Testowanie Systemu

```bash
# Uruchom testy RAG
python scripts/test_rag_system.py
```

## Najlepsze Praktyki

### 1. Organizacja Dokumentów

```
data/
├── docs/
│   ├── recipes/          # Przepisy
│   ├── guides/           # Przewodniki
│   ├── nutrition/        # Informacje o żywieniu
│   └── cooking/          # Techniki gotowania
├── uploads/              # Pliki uploadowane przez użytkowników
└── vector_db/            # Vector store (automatycznie generowany)
```

### 2. Metadane

Zawsze dodawaj odpowiednie metadane:

```python
metadata = {
    "type": "recipe",           # Typ dokumentu
    "category": "main_dish",    # Kategoria
    "tags": ["chicken", "healthy", "quick"],  # Tagi
    "author": "Chef AI",        # Autor
    "difficulty": "easy",       # Poziom trudności
    "cooking_time": "30min"     # Czas gotowania
}
```

### 3. Regularna Synchronizacja

```python
# Automatyczna synchronizacja po dodaniu paragonu
async def after_receipt_upload(receipt_id: int):
    await rag_integration.sync_receipts_to_rag(db)

# Automatyczna synchronizacja po zmianie spiżarni
async def after_pantry_update():
    await rag_integration.sync_pantry_to_rag(db)
```

### 4. Optymalizacja Wydajności

- Używaj odpowiednich rozmiarów chunków (1000-1500 tokenów)
- Ustaw nakładanie się na 10-20% rozmiaru chunka
- Regularnie czyść stare dokumenty
- Monitoruj użycie pamięci vector store

## Rozwiązywanie Problemów

### Częste Problemy

1. **Brak wyników wyszukiwania**
   - Sprawdź próg podobieństwa (`min_similarity`)
   - Upewnij się, że dokumenty zostały przetworzone
   - Sprawdź logi przetwarzania

2. **Wolne wyszukiwanie**
   - Zoptymalizuj rozmiar chunków
   - Rozważ użycie Pinecone dla większych zbiorów
   - Sprawdź indeksy vector store

3. **Błędy przetwarzania dokumentów**
   - Sprawdź format pliku
   - Upewnij się, że LangChain jest zainstalowany
   - Sprawdź uprawnienia do plików

### Debugowanie

```python
import logging

# Włącz debug logging
logging.getLogger("src.backend.core.rag_document_processor").setLevel(logging.DEBUG)
logging.getLogger("src.backend.core.vector_store").setLevel(logging.DEBUG)

# Sprawdź stan vector store
stats = await vector_store.get_statistics()
print(f"Vector store stats: {stats}")

# Sprawdź konkretny dokument
results = await vector_store.search("test query", k=1)
if results:
    print(f"Sample result: {results[0]}")
```

## Rozszerzenia i Przyszłe Funkcje

### Planowane Funkcje

1. **Multimodal RAG**
   - Obsługa obrazów przepisów
   - OCR dla zdjęć paragonów
   - Wideo tutoriale gotowania

2. **Hierarchiczny RAG**
   - Strukturyzowane kategorie
   - Relacje między dokumentami
   - Graf wiedzy

3. **Personalizacja**
   - Preferencje użytkownika
   - Historia wyszukiwań
   - Rekomendacje

4. **Real-time Updates**
   - WebSocket dla live updates
   - Automatyczna synchronizacja
   - Notifications o nowych dokumentach

---

Ten przewodnik zawiera wszystkie informacje potrzebne do efektywnego używania systemu RAG w aplikacji FoodSave AI. System jest zaprojektowany do łatwej rozbudowy i dostosowania do specyficznych potrzeb aplikacji.
