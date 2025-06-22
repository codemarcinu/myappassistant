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
- `opentelemetry-instrumentation-sqlalchemy` - Instrumentacja SQLAlchemy dla baz danych
- `opentelemetry-instrumentation-httpx` - Instrumentacja klienta HTTP
- `opentelemetry-exporter-jaeger` - Eksporter do systemu Jaeger
- `prometheus-client` - Klient Prometheus dla metryk
- `prometheus-fastapi-instrumentator` - Instrumentacja FastAPI dla Prometheus

### 2. **Prometheus**

Prometheus służy do zbierania i przechowywania metryk z różnych komponentów systemu:
- Metryki wydajności aplikacji
- Metryki zasobów systemowych (CPU, pamięć, dysk)
- Metryki niestandardowe specyficzne dla aplikacji
- Alerty oparte na progach

### 3. **Grafana**

Grafana zapewnia wizualizację danych monitoringu:
- Dashboardy dla różnych aspektów systemu
- Wykresy metryk w czasie rzeczywistym
- Wizualizacja logów
- Alerty i powiadomienia

### 4. **Loki**

Loki to system agregacji logów, który:
- Zbiera logi z różnych komponentów
- Umożliwia wyszukiwanie i filtrowanie logów
- Integruje się z Grafaną dla wizualizacji
- Zapewnia długoterminowe przechowywanie logów

#### Konfiguracja Loki:

Loki wymaga specjalnej konfiguracji, aby działać poprawnie:

```yaml
loki:
  image: grafana/loki:2.9.6
  container_name: foodsave-loki
  user: "0:0"  # Uruchom jako root, aby uniknąć problemów z uprawnieniami
  volumes:
    - ./monitoring/loki-config.yaml:/etc/loki/local-config.yaml
    - loki_data:/loki  # Używaj nazwanego wolumenu zamiast lokalnego katalogu
```

> **Uwaga**: Uruchomienie Loki jako root (user: "0:0") jest konieczne, aby uniknąć problemów z uprawnieniami podczas zapisywania danych. W środowisku produkcyjnym należy rozważyć bardziej bezpieczne rozwiązanie.

### 5. **Promtail**

Promtail to agent zbierający logi dla Loki:
- Śledzi pliki logów
- Przesyła logi do Loki
- Dodaje etykiety i metadane
- Obsługuje różne formaty logów (JSON, syslog, itp.)

## Konfiguracja i Uruchomienie

### Uruchamianie systemu monitoringu:

```bash
docker compose --profile monitoring --profile logging up -d
```

### Dostęp do interfejsów:

- Grafana: http://localhost:3001 (domyślne dane: admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

## Rozwiązywanie problemów

### Problemy z uprawnieniami Loki

Jeśli w logach Loki pojawiają się błędy typu:

```
level=error ts=2025-06-22T19:36:01.199521567Z caller=flush.go:143 org_id=fake msg="failed to flush" err="failed to flush chunks: store put chunk: open /loki/chunks/fake/210dd47453d74b0d/MTk3OTkxMzIxM2U6MTk3OTkxM2U1ZTA6ZTg2OTk1NGM=: permission denied
```

Rozwiązania:
1. Uruchom Loki jako root (user: "0:0")
2. Użyj nazwanego wolumenu Docker zamiast montowania lokalnego katalogu
3. Upewnij się, że katalog docelowy ma odpowiednie uprawnienia

### Problemy z siecią Docker

Jeśli występują konflikty sieci:

```
failed to create network foodsave-network: Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
```

Rozwiązania:
1. Usuń definicję sieci z pliku docker-compose.yaml i pozwól Docker Compose utworzyć ją automatycznie
2. Zatrzymaj wszystkie kontenery i sieci przed ponownym uruchomieniem
3. Użyj `docker network prune` aby usunąć nieużywane sieci

## Dobre praktyki

1. Regularnie monitoruj dashboardy Grafana
2. Ustaw alerty dla kluczowych metryk
3. Analizuj logi w przypadku problemów
4. Utrzymuj odpowiednią retencję danych
5. Twórz kopie zapasowe konfiguracji dashboardów

## Przyszły rozwój

- Implementacja distributed tracingu z Jaeger
- Rozszerzenie metryk specyficznych dla aplikacji
- Automatyczne alerty przez email/Slack
- Integracja z systemami CI/CD
