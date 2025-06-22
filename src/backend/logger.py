import logging
import os
import sys


def setup_logger(name="backend", level=logging.INFO):
    """Konfiguruje i zwraca logger. Loguje do konsoli i do pliku logs/backend/app.log"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Unikaj duplikowania handlerów
    if not logger.handlers:
        # Format logów
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Handler dla konsoli
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Handler dla pliku
        log_dir = os.path.join(os.path.dirname(__file__), "../../logs/backend")
        log_dir = os.path.abspath(log_dir)
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Konfiguracja root loggera, aby przechwytywać wszystkie logi
def configure_root_logger(level=logging.INFO):
    """Konfiguruje root logger do zapisywania wszystkich logów do pliku"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Usuń istniejące handlery, aby uniknąć duplikacji
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Format logów
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Handler dla pliku
    log_dir = os.path.join(os.path.dirname(__file__), "../../logs/backend")
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


# Utwórz domyślny logger
logger = setup_logger()

# Skonfiguruj root logger, aby przechwytywać wszystkie logi
configure_root_logger()

# Ustaw poziom logowania dla niektórych głośnych loggerów
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
