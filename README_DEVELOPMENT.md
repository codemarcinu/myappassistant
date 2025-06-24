## Automatyczna naprawa błędów typów i składniowych (Python)

W projekcie znajduje się skrypt `fix_syntax_errors.py`, który automatycznie naprawia najczęstsze błędy składniowe związane z typowaniem (np. `param -> Any: str` na `param: str`).

### Jak używać?

1. Upewnij się, że jesteś w katalogu głównym projektu.
2. Uruchom skrypt:
   ```bash
   python3 fix_syntax_errors.py
   ```
3. Po zakończeniu uruchom:
   ```bash
   python3 -m mypy src/backend --show-error-codes
   ```
   aby sprawdzić, czy nie ma już błędów typowania/składniowych.

### Co robi skrypt?
- Przeszukuje wszystkie pliki `.py` w `src/backend/`
- Automatycznie poprawia powtarzalne błędy typów/adnotacji
- Wypisuje listę naprawionych plików

### Kiedy uruchamiać?
- Po masowych zmianach w typowaniu
- Po migracji kodu lub automatycznych refaktoryzacjach
- Przed uruchomieniem testów typowania (`mypy`)

### Bezpieczeństwo
- Skrypt nie usuwa kodu, tylko poprawia adnotacje typów
- Zalecane commitowanie zmian po każdej automatycznej naprawie
