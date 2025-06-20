# Backup System Guide - FoodSave AI

## Przegląd

System backup dla aplikacji FoodSave AI implementuje **najlepsze praktyki branżowe** zgodnie z regułą **3-2-1** i rekomendacjami z [SimpleBackups](https://simplebackups.com/blog/database-backup-best-practices) oraz [ConnectWise](https://www.connectwise.com/blog/backup-strategy-best-practices).

## 🛡️ Reguła 3-2-1

System backup implementuje **regułę 3-2-1**:
- **3 kopie** danych
- **2 różne typy** nośników
- **1 kopia** poza lokalizacją

## Architektura Systemu

### Komponenty Backup

1. **Database Backup** - Pełny dump bazy danych SQLite
2. **Files Backup** - Ważne pliki i katalogi aplikacji
3. **Configuration Backup** - Ustawienia i konfiguracja
4. **Vector Store Backup** - Dane systemu RAG

### Struktura Katalogów

```
backups/
├── database/          # Backup bazy danych
├── files/            # Backup plików
├── config/           # Backup konfiguracji
├── vector_store/     # Backup vector store
└── *.json           # Manifesty backupów
```

## 🚀 Szybki Start

### 1. Tworzenie Backupu

#### Przez API:
```bash
curl -X POST "http://localhost:8000/api/v2/backup/create?verify=true"
```

#### Przez CLI:
```bash
python scripts/backup_cli.py create --name "pre_deployment_backup"
```

#### Przez Frontend:
- Przejdź do `/backup`
- Kliknij "Create Full Backup"

### 2. Lista Backupów

#### Przez API:
```bash
curl "http://localhost:8000/api/v2/backup/list"
```

#### Przez CLI:
```bash
python scripts/backup_cli.py list
```

### 3. Przywracanie Backupu

#### Przez API:
```bash
curl -X POST "http://localhost:8000/api/v2/backup/restore/backup_name"
```

#### Przez CLI:
```bash
python scripts/backup_cli.py restore backup_name --components database,files
```

## 📊 Statystyki i Monitoring

### Pobieranie Statystyk

```bash
# API
curl "http://localhost:8000/api/v2/backup/stats"

# CLI
python scripts/backup_cli.py stats
```

### Health Check

```bash
curl "http://localhost:8000/api/v2/backup/health"
```

## 🔍 Weryfikacja Backupów

### Automatyczna Weryfikacja

Każdy backup jest automatycznie weryfikowany poprzez:
- **Checksum SHA-256** dla każdego pliku
- **Integralność archiwów** (ZIP, TAR.GZ)
- **Walidację manifestów** JSON

### Ręczna Weryfikacja

```bash
# API
curl -X POST "http://localhost:8000/api/v2/backup/verify/backup_name"

# CLI
python scripts/backup_cli.py verify backup_name
```

## 🧹 Polityka Retencji

System automatycznie zarządza retencją backupów:

### Ustawienia Domyślne
- **Backupy dzienne**: 7 dni
- **Backupy tygodniowe**: 4 tygodnie
- **Backupy miesięczne**: 12 miesięcy

### Czyszczenie Starych Backupów

```bash
# API
curl -X DELETE "http://localhost:8000/api/v2/backup/cleanup"

# CLI
python scripts/backup_cli.py cleanup
```

## 🔧 Konfiguracja

### Zmienne Środowiskowe

```bash
# Włączanie backupów do chmury
CLOUD_BACKUP_ENABLED=true

# Konfiguracja retencji
BACKUP_DAILY_RETENTION_DAYS=7
BACKUP_WEEKLY_RETENTION_WEEKS=4
BACKUP_MONTHLY_RETENTION_MONTHS=12

# Weryfikacja
BACKUP_VERIFY_ENABLED=true
BACKUP_CHECKSUM_VERIFICATION=true
```

### Dostosowanie Komponentów

W `src/backend/core/backup_manager.py`:

```python
# Dodanie nowego komponentu
async def _backup_custom_component(self, backup_name: str):
    # Implementacja backupu niestandardowego komponentu
    pass
```

## 📋 API Endpoints

### Backup Management API

| Endpoint | Method | Opis |
|----------|--------|------|
| `/api/v2/backup/create` | POST | Tworzenie backupu |
| `/api/v2/backup/list` | GET | Lista backupów |
| `/api/v2/backup/restore/{name}` | POST | Przywracanie backupu |
| `/api/v2/backup/verify/{name}` | POST | Weryfikacja backupu |
| `/api/v2/backup/stats` | GET | Statystyki systemu |
| `/api/v2/backup/cleanup` | DELETE | Czyszczenie starych backupów |
| `/api/v2/backup/health` | GET | Health check |

### Przykłady Żądań

#### Tworzenie Backupu z Nazwą
```bash
curl -X POST "http://localhost:8000/api/v2/backup/create?backup_name=my_backup&verify=true"
```

#### Przywracanie Wybranych Komponentów
```bash
curl -X POST "http://localhost:8000/api/v2/backup/restore/backup_name?components=database,files"
```

## 🛠️ CLI Tool

### Instalacja

```bash
chmod +x scripts/backup_cli.py
```

### Komendy

```bash
# Tworzenie backupu
python scripts/backup_cli.py create --name "backup_name"

# Lista backupów
python scripts/backup_cli.py list

# Przywracanie
python scripts/backup_cli.py restore backup_name --components database,files

# Weryfikacja
python scripts/backup_cli.py verify backup_name

# Czyszczenie
python scripts/backup_cli.py cleanup

# Statystyki
python scripts/backup_cli.py stats
```

## 🔄 Automatyzacja

### Cron Job dla Automatycznych Backupów

```bash
# Dodaj do crontab (crontab -e)
0 2 * * * cd /path/to/foodsave && python scripts/backup_cli.py create
0 3 * * 0 cd /path/to/foodsave && python scripts/backup_cli.py cleanup
```

### Systemd Service

```ini
[Unit]
Description=FoodSave AI Backup Service
After=network.target

[Service]
Type=oneshot
User=foodsave
WorkingDirectory=/path/to/foodsave
ExecStart=/usr/bin/python3 scripts/backup_cli.py create
```

## 🚨 Troubleshooting

### Problemy z Backupem

#### Błąd: "Backup directory not writable"
```bash
# Sprawdź uprawnienia
ls -la backups/
chmod 755 backups/
chown foodsave:foodsave backups/
```

#### Błąd: "Database backup failed"
```bash
# Sprawdź połączenie z bazą
python -c "from src.backend.infrastructure.database.database import engine; print('DB OK')"
```

#### Błąd: "Verification failed"
```bash
# Sprawdź integralność plików
python scripts/backup_cli.py verify backup_name
```

### Logi

```bash
# Logi aplikacji
tail -f logs/app.log | grep backup

# Logi CLI
python scripts/backup_cli.py create 2>&1 | tee backup.log
```

## 📈 Monitoring i Alerty

### Integracja z Systemami Monitoringu

```python
# Przykład integracji z Prometheus
from prometheus_client import Counter, Gauge

backup_counter = Counter('backup_total', 'Total backups created')
backup_size_gauge = Gauge('backup_size_bytes', 'Backup size in bytes')

# W backup_manager.py
backup_counter.inc()
backup_size_gauge.set(total_size)
```

### Alerty

```python
# Przykład alertu o nieudanym backupie
async def send_backup_alert(error_message):
    # Integracja z Slack, Email, etc.
    pass
```

## 🔐 Bezpieczeństwo

### Szyfrowanie Backupów

```python
# Przykład szyfrowania (do implementacji)
import cryptography.fernet

def encrypt_backup(backup_file, key):
    f = cryptography.fernet.Fernet(key)
    with open(backup_file, 'rb') as file:
        encrypted_data = f.encrypt(file.read())
    return encrypted_data
```

### Zarządzanie Sekretami

```bash
# Używanie zmiennych środowiskowych
export BACKUP_ENCRYPTION_KEY="your-secret-key"
export CLOUD_ACCESS_KEY="your-cloud-key"
```

## 📚 Najlepsze Praktyki

### Zgodnie z Industry Standards

1. **Regularne Backupy** - Codzienne automatyczne backupy
2. **Weryfikacja** - Automatyczna weryfikacja integralności
3. **Retencja** - Polityka retencji dostosowana do potrzeb
4. **Off-site Storage** - Kopie poza lokalizacją
5. **Testowanie Przywracania** - Regularne testy restore
6. **Dokumentacja** - Szczegółowa dokumentacja procedur

### Rekomendacje dla Produkcji

1. **Backup przed Deploy** - Zawsze przed wdrożeniem
2. **Monitoring** - Alerty o nieudanych backupach
3. **Testowanie** - Regularne testy na środowisku testowym
4. **Dokumentacja** - Procedury disaster recovery
5. **Audyt** - Regularne audyty systemu backup

## 🔗 Integracje

### Cloud Storage

```python
# Przykład integracji z AWS S3
import boto3

async def upload_to_s3(backup_file, bucket_name):
    s3 = boto3.client('s3')
    s3.upload_file(backup_file, bucket_name, f"backups/{backup_file}")
```

### Monitoring Tools

- **Prometheus** - Metryki backupów
- **Grafana** - Dashboardy
- **AlertManager** - Alerty
- **Slack/Teams** - Powiadomienia

## 📞 Wsparcie

### Debugowanie

```bash
# Włączanie debug logów
export LOG_LEVEL=DEBUG
python scripts/backup_cli.py create

# Sprawdzanie szczegółów backupu
python scripts/backup_cli.py list
python scripts/backup_cli.py verify backup_name
```

### Kontakt

W przypadku problemów z systemem backup:
1. Sprawdź logi aplikacji
2. Uruchom health check
3. Sprawdź uprawnienia katalogów
4. Zweryfikuj konfigurację

---

**System backup FoodSave AI** zapewnia **profesjonalną ochronę danych** zgodnie z **najlepszymi praktykami branżowymi** i **regułą 3-2-1**.
