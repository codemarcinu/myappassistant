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
- `opentelemetry-instrumentation-sqlalchemy` - Śledzenie zapytań bazodanowych
- `opentelemetry-instrumentation-httpx` - Monitorowanie zapytań HTTP
- `opentelemetry-exporter-jaeger` - Eksport śladów do Jaeger

### 2. **Prometheus**

System zbierania i przechowywania metryk:
- Scraping metryk z endpointów HTTP
- Przechowywanie szeregów czasowych
- Alerting na podstawie reguł
- Integracja z Grafana

### 3. **Loki**

Agregacja i przeszukiwanie logów:
- Zbieranie logów z kontenerów
- Indeksowanie i przeszukiwanie
- Korelacja z metrykami i śladami
- Wizualizacja w Grafana

### 4. **Grafana**

Wizualizacja i dashboardy:
- Interaktywne dashboardy
- Łączenie danych z różnych źródeł
- Alerty i powiadomienia
- Udostępnianie i eksport raportów

## Implementacja w Kodzie

### Konfiguracja OpenTelemetry

```python
# src/backend/core/telemetry.py
def setup_telemetry(
    service_name: str = "foodsave-ai-backend",
    enable_jaeger: bool = True,
    enable_prometheus: bool = True,
    enable_console: bool = False,
) -> None:
    """Setup OpenTelemetry dla distributed tracing i metrics"""
    global tracer

    # Resource configuration
    resource = Resource.create({
        "service.name": service_name,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.ENVIRONMENT,
    })

    # Trace provider setup
    trace_provider = TracerProvider(resource=resource)

    # Jaeger exporter
    if enable_jaeger:
        jaeger_endpoint = os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
        jaeger_exporter = JaegerExporter(collector_endpoint=jaeger_endpoint)
        trace_provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))

    # Set global trace provider
    trace.set_tracer_provider(trace_provider)
    tracer = trace.get_tracer(__name__)

    # Metrics setup
    if enable_prometheus:
        setup_prometheus_metrics()
```

### Instrumentacja FastAPI

```python
# src/backend/app_factory.py
from backend.core.telemetry import setup_telemetry, instrument_httpx, instrument_sqlalchemy

def create_app():
    app = FastAPI()

    # Setup telemetry
    setup_telemetry()

    # Instrument HTTPX client
    instrument_httpx()

    # Instrument SQLAlchemy (after engine creation)
    instrument_sqlalchemy(engine)
```

### Śledzenie Funkcji

```python
# Przykład użycia dekoratora
from backend.core.telemetry import traced_function, traced_async_function

@traced_function(name="process_shopping_list")
def process_shopping_list(items):
    # Kod funkcji
    pass

@traced_async_function(name="fetch_product_data")
async def fetch_product_data(product_id):
    # Kod asynchronicznej funkcji
    pass
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
