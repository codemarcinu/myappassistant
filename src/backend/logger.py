from __future__ import annotations
import logging
import os
import sys
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, List, Optional, Union, Callable
from typing import AsyncGenerator, Coroutine


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging to be parsed by Loki/Promtail"""

    def format(self, record) -> None:
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "message": record.getMessage(),
        }

        # Include exception info if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include custom attributes if available
        for key, value in record.__dict__.items():
            if key not in ["args", "asctime", "created", "exc_info", "exc_text", "filename",
                          "funcName", "levelname", "lineno", "message", "module",
                          "msecs", "msg", "name", "pathname", "process",
                          "processName", "relativeCreated", "stack_info", "thread",
                          "threadName"]:
                log_data[key] = value

        return json.dumps(log_data)


def setup_logger(name="backend", level=logging.INFO) -> None:
    """Konfiguruje i zwraca logger z formatem JSON dla integracji z Loki"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Usuń istniejące handlery, aby uniknąć duplikacji
    if logger.handlers:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)

    # Format JSON
    json_formatter = JsonFormatter()

    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)

    # Handler dla pliku z rotacją (10MB max, zachowaj 5 kopii)
    log_dir = os.path.join(os.path.dirname(__file__), "../../logs/backend")
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)

    return logger


# Konfiguracja root loggera, aby przechwytywać wszystkie logi
def configure_root_logger(level=logging.INFO) -> None:
    """Konfiguruje root logger z formatem JSON"""
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Usuń istniejące handlery, aby uniknąć duplikacji
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Format JSON
    json_formatter = JsonFormatter()

    # Handler dla konsoli
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(json_formatter)
    root_logger.addHandler(console_handler)

    # Handler dla pliku z rotacją
    log_dir = os.path.join(os.path.dirname(__file__), "../../logs/backend")
    log_dir = os.path.abspath(log_dir)
    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(json_formatter)
    root_logger.addHandler(file_handler)


# Utwórz domyślny logger
logger = setup_logger()

# Skonfiguruj root logger, aby przechwytywać wszystkie logi
configure_root_logger()

# Ustaw poziom logowania dla niektórych głośnych loggerów
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
