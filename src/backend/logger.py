import logging
import sys


def setup_logger(name="backend", level=logging.INFO):
    """Konfiguruje i zwraca logger"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Unikaj duplikowania handlerów
    if not logger.handlers:
        # Handler dla konsoli
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)

        # Format logów
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

    return logger


# Utwórz domyślny logger
logger = setup_logger()
