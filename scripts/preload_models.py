#!/usr/bin/env python3
"""
Skrypt do pre-pobierania modeli AI
Uruchamiany podczas budowania obrazu Docker, aby uniknąć pobierania przy każdym uruchomieniu
"""

import logging
import os
import sys
from pathlib import Path

# Dodaj ścieżkę do modułów backend
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def preload_mmlw_model():
    """Pre-pobiera model MMLW embeddingów"""
    try:
        logger.info("Pre-downloading MMLW embedding model...")

        # Ustaw zmienne środowiskowe dla cache
        os.environ["HF_HOME"] = "/app/.cache/huggingface"
        os.environ["TRANSFORMERS_CACHE"] = "/app/.cache/huggingface/transformers"

        # Import i pobieranie modelu
        from transformers import AutoModel, AutoTokenizer

        model_name = "sdadas/mmlw-retrieval-roberta-base"

        logger.info(f"Downloading tokenizer for {model_name}...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)

        logger.info(f"Downloading model {model_name}...")
        model = AutoModel.from_pretrained(model_name)

        logger.info("MMLW model downloaded successfully!")
        return True

    except Exception as e:
        logger.error(f"Failed to preload MMLW model: {e}")
        return False


def preload_ollama_models():
    """Pre-pobiera modele Ollama (jeśli dostępne)"""
    try:
        logger.info("Checking for Ollama models to preload...")

        # Lista modeli do pre-pobrania
        models_to_preload = [
            "llama2:7b",  # Podstawowy model
            "llama2:13b",  # Większy model dla złożonych zadań
        ]

        # Sprawdź czy Ollama jest dostępne
        import requests

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(
                    "Ollama is available, models will be downloaded on first use"
                )
            else:
                logger.warning(
                    "Ollama not responding, models will be downloaded when needed"
                )
        except:
            logger.warning(
                "Ollama not available, models will be downloaded when needed"
            )

    except Exception as e:
        logger.warning(f"Could not check Ollama models: {e}")


def main():
    """Główna funkcja pre-pobierania modeli"""
    logger.info("Starting model preloading...")

    # Pre-pobierz model MMLW
    mmlw_success = preload_mmlw_model()

    # Sprawdź modele Ollama
    preload_ollama_models()

    if mmlw_success:
        logger.info("Model preloading completed successfully!")
        return 0
    else:
        logger.error("Model preloading failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
