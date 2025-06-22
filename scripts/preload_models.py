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

        # Sprawdź czy Ollama jest dostępne
        import requests
        import subprocess

        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama is available, preloading Bielik-4.5B-v3.0-Instruct model...")
                
                # Tworzenie pliku Modfile dla Bielik-4.5B
                template = 'TEMPLATE """{{ if .System }}system\n\n{{ .System }}{{ end }}{{ if .Prompt }}user\n\n{{ .Prompt }}{{ end }}assistant\n\n{{ .Response }}"""'
                
                with open("/tmp/Bielik-4.5B.modfile", "w") as f:
                    f.write(f"""
FROM ./Bielik-4.5B-v3.0-Instruct.Q8_0.gguf

{template}

PARAMETER stop ""
PARAMETER stop ""
PARAMETER stop ""
PARAMETER temperature 0.1
                    """)
                
                # Pobieranie modelu
                try:
                    subprocess.run(["ollama", "pull", "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"], check=True)
                    logger.info("Bielik-4.5B-v3.0-Instruct model preloaded successfully!")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to pull Bielik model: {e}")
            else:
                logger.warning(
                    "Ollama not responding, models will be downloaded when needed"
                )
        except Exception as e:
            logger.warning(
                f"Ollama not available, models will be downloaded when needed: {e}"
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
