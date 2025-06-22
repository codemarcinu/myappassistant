# Implementacja Strumieniowania Odpowiedzi w FoodSave AI

## Wprowadzenie

Implementacja strumieniowania odpowiedzi (streaming) jest kluczowym elementem optymalizacji percepcji wydajności systemu FoodSave AI. Dzięki strumieniowaniu, użytkownik widzi odpowiedź pojawiającą się stopniowo, słowo po słowie, zamiast czekać na całą odpowiedź. To znacząco poprawia wrażenia użytkownika, szczególnie przy dłuższych odpowiedziach.

## Architektura Strumieniowania

Implementacja strumieniowania obejmuje zmiany na trzech poziomach:

1. **Backend (Serwer)**:
   - Modyfikacja `Orchestrator` do obsługi strumieniowania
   - Aktualizacja `AgentRouter` do przekazywania odpowiedzi strumieniowych
   - Dodanie metody `process_stream` do agentów
   - Obsługa strumieniowania w endpointach API

2. **Frontend (Klient)**:
   - Aktualizacja hooka `useChat` do obsługi wiadomości strumieniowych
   - Modyfikacja komponentów UI do wyświetlania strumieniowanych odpowiedzi
   - Dodanie wizualnych wskaźników aktywnego strumieniowania

3. **Komunikacja**:
   - Wykorzystanie formatu NDJSON dla przesyłania strumieniowanych odpowiedzi
   - Obsługa callbacków dla przetwarzania fragmentów odpowiedzi

## Kluczowe Komponenty

### Backend

#### 1. Orchestrator

Dodano parametr `stream` i `stream_callback` do metody `process_command`, co pozwala na:
- Uruchomienie agentów w trybie strumieniowania
- Przekazywanie fragmentów odpowiedzi przez callback
- Obsługę błędów w trybie strumieniowym

#### 2. AgentRouter

Rozszerzono metodę `route_to_agent` o:
- Obsługę parametru `stream`
- Wykrywanie czy agent obsługuje strumieniowanie
- Fallback do standardowej odpowiedzi jeśli agent nie obsługuje strumieniowania

#### 3. GeneralConversationAgent

Dodano metodę `process_stream`, która:
- Równolegle pobiera kontekst z RAG i internetu
- Informuje użytkownika o postępie przetwarzania
- Strumieniowo przekazuje odpowiedź z modelu LLM
- Obsługuje błędy w sposób przyjazny dla użytkownika

#### 4. API Endpoints

Zmodyfikowano endpoint `/memory_chat` do:
- Odbierania żądań z parametrami strumieniowania
- Przekazywania fragmentów odpowiedzi jako NDJSON
- Obsługi błędów w strumieniu

### Frontend

#### 1. useChat Hook

Rozszerzono hook o:
- Stan dla aktualnie strumieniowanej wiadomości
- Obsługę fragmentów odpowiedzi w czasie rzeczywistym
- Aktualizację UI w miarę napływania nowych fragmentów

#### 2. MessageList i MessageItem

Zaktualizowano komponenty do:
- Wyświetlania aktualnie strumieniowanej wiadomości
- Pokazywania wskaźnika aktywnego strumieniowania (kursor)
- Automatycznego przewijania do najnowszej wiadomości

## Przepływ Danych

1. Użytkownik wysyła wiadomość przez interfejs
2. Frontend tworzy pustą wiadomość asystenta i rozpoczyna strumieniowanie
3. Backend przetwarza zapytanie i rozpoczyna generowanie odpowiedzi
4. Fragmenty odpowiedzi są przesyłane do frontendu w miarę ich generowania
5. Frontend aktualizuje UI, pokazując pojawiające się fragmenty tekstu
6. Po zakończeniu strumieniowania, kompletna wiadomość jest dodawana do historii

## Korzyści

- **Szybsza Percepcja Odpowiedzi**: Użytkownik widzi pierwsze słowa natychmiast
- **Lepsza Interaktywność**: System wydaje się bardziej responsywny
- **Transparentność Procesu**: Użytkownik widzi, że system aktywnie pracuje
- **Redukcja Frustracji**: Eliminacja długiego czekania bez informacji zwrotnej

## Przyszłe Ulepszenia

- Dodanie wskaźników postępu dla operacji w tle (np. wyszukiwanie RAG)
- Implementacja anulowania strumieniowania przez użytkownika
- Optymalizacja buforowania dla jeszcze szybszej pierwszej odpowiedzi
- Rozszerzenie strumieniowania na wszystkie typy agentów
