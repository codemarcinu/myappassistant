# Monitoring i Telemetria - FoodSave AI

## Wprowadzenie

System monitoringu i telemetrii w FoodSave AI zapewnia kompleksowy wgląd w działanie aplikacji, umożliwiając śledzenie wydajności, diagnozowanie problemów i optymalizację zasobów. Implementacja opiera się na standardach OpenTelemetry i wykorzystuje popularne narzędzia open-source.

## Komponenty Systemu

### 1. **OpenTelemetry**

OpenTelemetry służy jako podstawa systemu telemetrii, zapewniając:
- Distributed tracing
- Metryki wydajności
- Logowanie zdarzeń
- Instrumentację automatyczną dla popularnych bibliotek

#### Zaimplementowane pakiety:
- `opentelemetry-api` - API dla instrumentacji kodu
- `opentelemetry-sdk` - Implementacja SDK
- `opentelemetry-instrumentation-fastapi` - Automatyczna instrumentacja FastAPI
- `opentelemetry-instrumentation-sqlalchemy` - Instrumentacja dla SQLAlchemy
- `opentelemetry-instrumentation-httpx` - Instrumentacja dla HTTPX
- `opentelemetry-exporter-jaeger` - Eksporter do Jaeger
- `prometheus-client` - Klient Prometheus
- `prometheus-fastapi-instrumentator` - Instrumentacja FastAPI dla Prometheus

### 2. **Prometheus**

Prometheus zbiera metryki z aplikacji i infrastruktury:
- Liczba zapytań
- Czas odpowiedzi
- Użycie zasobów (CPU, pamięć)
- Metryki niestandardowe

### 3. **Grafana**

Grafana wizualizuje zebrane metryki:
- Interaktywne dashboardy
- Alerty
- Analizy trendów

### 4. **Loki**

Loki agreguje i przeszukuje logi:
- Centralizacja logów
- Korelacja z metrykami
- Etykietowanie i filtrowanie

## Konfiguracja Systemu

### Konfiguracja OpenTelemetry w Backend

Backend wykorzystuje OpenTelemetry do śledzenia zapytań i metryk wydajności. Pakiety zostały dodane do `requirements.txt` i są automatycznie instalowane podczas budowania obrazu Docker.

### Niestandardowy Obraz Ollama

Dla zapewnienia poprawnych health checków, używamy niestandardowego obrazu Ollama z zainstalowanym curl:

```dockerfile
FROM ollama/ollama:latest

# Instalacja curl
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Kontynuuj z oryginalną konfiguracją
CMD ["serve"]
```

Health check w docker-compose.yaml używa curl do sprawdzenia, czy API Ollama jest dostępne:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:11434/api/version || exit 1"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 120s
```

### Konfiguracja Prometheus

Prometheus jest skonfigurowany do zbierania metryk z backendu FastAPI oraz innych komponentów systemu. Konfiguracja znajduje się w pliku `monitoring/prometheus.yml`.

### Konfiguracja Grafana

Grafana jest skonfigurowana do wyświetlania metryk z Prometheus i logów z Loki. Dashboardy są dostępne w katalogu `monitoring/grafana/dashboards`.

## Uruchomienie Systemu Monitoringu

System monitoringu można uruchomić za pomocą profilu `monitoring` w docker-compose:

```bash
docker compose up -d --profile monitoring
```

Dostęp do interfejsów:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001 (domyślne dane logowania: admin/admin)

## Rozwiązywanie Problemów

### Problemy z Health Checkami

Jeśli kontenery są oznaczone jako "unhealthy", sprawdź:
1. Czy usługi są dostępne na oczekiwanych portach
2. Czy narzędzia używane w health checkach (np. curl) są dostępne w kontenerach
3. Czy parametry health checków (timeout, retries) są odpowiednio skonfigurowane

### Problemy z Metrykami

Jeśli metryki nie są widoczne w Prometheus/Grafana:
1. Sprawdź, czy instrumentacja OpenTelemetry jest poprawnie skonfigurowana
2. Sprawdź, czy Prometheus ma dostęp do endpointów z metrykami
3. Zweryfikuj konfigurację data source w Grafana

## Dobre Praktyki

1. Używaj znaczących nazw dla metryk i logów
2. Dodawaj odpowiednie etykiety do metryk dla lepszej filtracji
3. Koreluj logi z metrykami za pomocą identyfikatorów trace
4. Regularnie przeglądaj dashboardy w poszukiwaniu anomalii

## Przydatne Polecenia

```bash
# Sprawdzenie logów serwisów monitoringu
docker compose logs prometheus
docker compose logs grafana

# Sprawdzenie statusu health checków
docker ps

# Restart usług monitoringu
docker compose restart prometheus grafana
```

## Uruchamianie Systemu Monitoringu

### Lokalne Środowisko

```bash
# Uruchomienie systemu monitoringu
./scripts/start_monitoring.sh

# Sprawdzenie statusu
docker compose ps
```

### Dostęp do Interfejsów

- **Grafana**: http://localhost:3030 (admin/foodsave)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100

## Dostępne Dashboardy

### 1. Główny Dashboard FoodSave

Zawiera podstawowe metryki aplikacji:
- Liczba zapytań HTTP
- Czas odpowiedzi
- Błędy i wyjątki
- Wykorzystanie zasobów

### 2. Dashboard Interakcji Czatu

Dedykowany do monitorowania interakcji z czatem:
- Liczba wiadomości
- Czas generowania odpowiedzi
- Wykorzystanie modeli AI
- Błędy w przetwarzaniu

## Konfiguracja Alertów

System zawiera predefiniowane reguły alertów:

1. **High Error Rate**
   - Trigger: >5% zapytań z błędami w ciągu 5 minut
   - Severity: critical

2. **Slow Response Time**
   - Trigger: średni czas odpowiedzi >2s w ciągu 5 minut
   - Severity: warning

3. **Database Connection Errors**
   - Trigger: błędy połączenia z bazą danych
   - Severity: critical

## Rozwiązywanie Problemów

### Problem: Brak danych w Grafana

```bash
# Sprawdź status źródeł danych
curl -s http://localhost:3030/api/datasources | jq

# Sprawdź logi Prometheus
docker compose logs prometheus

# Sprawdź logi Loki
docker compose logs loki
```

### Problem: Brak metryk z aplikacji

```bash
# Sprawdź endpoint metryk
curl -s http://localhost:8000/metrics

# Sprawdź logi aplikacji
docker compose logs backend | grep -i "metrics\|telemetry\|opentelemetry"
```

## Rozszerzenia

### Dodawanie Własnych Metryk

```python
from prometheus_client import Counter, Histogram

# Licznik zapytań
request_counter = Counter(
    'app_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

# Histogram czasów odpowiedzi
response_time = Histogram(
    'app_response_time_seconds',
    'Response time in seconds',
    ['method', 'endpoint']
)

# Użycie w kodzie
def process_request():
    request_counter.labels(method='GET', endpoint='/api/data', status='200').inc()

    with response_time.labels(method='GET', endpoint='/api/data').time():
        # Kod obsługujący zapytanie
        pass
```

### Dodawanie Własnych Dashboardów

1. Zaloguj się do Grafana (http://localhost:3030)
2. Wybierz "Create" > "Dashboard"
3. Dodaj nowe panele z metrykami
4. Zapisz dashboard w katalogu `monitoring/grafana/dashboards/`

## Podsumowanie

Implementacja systemu monitoringu i telemetrii w FoodSave AI zapewnia:

- **Kompleksowy wgląd** w działanie aplikacji
- **Szybką diagnostykę** problemów
- **Śledzenie wydajności** w czasie rzeczywistym
- **Alerty** o potencjalnych problemach
- **Wizualizację danych** dla łatwiejszej analizy

System jest skalowalny i może być rozszerzany o dodatkowe metryki, dashboardy i alerty w miarę rozwoju aplikacji.
