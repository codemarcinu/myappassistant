#!/usr/bin/env python3
"""
Skrypt do testowania napraw systemu FoodSave AI
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict

# Dodaj katalog projektu do PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backend.agents.search_agent import SearchAgent
from src.backend.agents.weather_agent import WeatherAgent
from src.backend.config import settings
from src.backend.core.exceptions import BaseCustomException, ValidationError
from src.backend.core.hybrid_llm_client import hybrid_llm_client
from src.backend.core.perplexity_client import perplexity_client

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_llm_models():
    """Test dostępności modeli językowych"""
    print("\n=== Test modeli językowych ===")

    try:
        # Test głównego modelu
        print(f"Testowanie modelu: {settings.OLLAMA_MODEL}")
        response = await hybrid_llm_client.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": "Jesteś pomocnym asystentem."},
                {"role": "user", "content": "Powiedz 'cześć' po polsku."},
            ],
            stream=False,
        )

        if response and response.get("message"):
            print(f"✅ Model {settings.OLLAMA_MODEL} działa poprawnie")
            print(f"Odpowiedź: {response['message']['content']}")
        else:
            print(f"❌ Model {settings.OLLAMA_MODEL} nie odpowiada poprawnie")

    except Exception as e:
        print(f"❌ Błąd testowania modelu {settings.OLLAMA_MODEL}: {e}")

    # Test dostępnych modeli
    print(f"\nDostępne modele: {settings.AVAILABLE_MODELS}")

    for model in settings.AVAILABLE_MODELS[:2]:  # Testuj tylko pierwsze 2
        try:
            print(f"Testowanie modelu: {model}")
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[{"role": "user", "content": "Test"}],
                stream=False,
            )

            if response and response.get("message"):
                print(f"✅ Model {model} dostępny")
            else:
                print(f"⚠️ Model {model} nie odpowiada poprawnie")

        except Exception as e:
            print(f"❌ Model {model} niedostępny: {e}")


async def test_perplexity_api():
    """Test API Perplexity"""
    print("\n=== Test API Perplexity ===")

    try:
        # Test połączenia
        test_result = await perplexity_client.test_connection()
        print(f"Test połączenia: {test_result}")

        if test_result["success"]:
            print("✅ API Perplexity działa poprawnie")
        else:
            print(f"❌ API Perplexity nie działa: {test_result['error']}")

    except Exception as e:
        print(f"❌ Błąd testowania API Perplexity: {e}")

    # Test dostępnych modeli
    try:
        available_models = await perplexity_client.get_available_models()
        print(
            f"Dostępne modele Perplexity: {available_models[:5]}..."
        )  # Pokaż pierwsze 5
    except Exception as e:
        print(f"❌ Błąd pobierania modeli Perplexity: {e}")


async def test_search_agent():
    """Test SearchAgent"""
    print("\n=== Test SearchAgent ===")

    try:
        agent = SearchAgent()

        # Test podstawowego wyszukiwania
        test_query = "przepis na pierogi"
        print(f"Testowanie wyszukiwania: '{test_query}'")

        response = await agent.process(
            {"query": test_query, "model": settings.OLLAMA_MODEL}
        )

        if response.success:
            print("✅ SearchAgent działa poprawnie")
            print(f"Odpowiedź: {response.text[:200]}...")
        else:
            print(f"❌ SearchAgent błąd: {response.error}")

    except Exception as e:
        print(f"❌ Błąd testowania SearchAgent: {e}")


async def test_weather_agent():
    """Test WeatherAgent"""
    print("\n=== Test WeatherAgent ===")

    try:
        agent = WeatherAgent()

        # Test pogody dla Warszawy
        test_location = "Warszawa"
        print(f"Testowanie pogody dla: {test_location}")

        response = await agent.process(
            {"location": test_location, "model": settings.OLLAMA_MODEL}
        )

        if response.success:
            print("✅ WeatherAgent działa poprawnie")
            print(f"Odpowiedź: {response.text[:200]}...")
        else:
            print(f"❌ WeatherAgent błąd: {response.error}")

    except Exception as e:
        print(f"❌ Błąd testowania WeatherAgent: {e}")


async def test_exception_handling():
    """Test obsługi wyjątków"""
    print("\n=== Test obsługi wyjątków ===")

    try:
        # Test ValidationError
        print("Testowanie ValidationError...")
        raise ValidationError("Test błędu walidacji", field="test_field")
    except ValidationError as e:
        print(f"✅ ValidationError przechwycony: {e.message}")
        print(f"Szczegóły: {e.to_dict()}")

    try:
        # Test BaseCustomException
        print("Testowanie BaseCustomException...")
        raise BaseCustomException(
            "Test błędu niestandardowego", error_code="TEST_ERROR"
        )
    except BaseCustomException as e:
        print(f"✅ BaseCustomException przechwycony: {e.message}")
        print(f"Szczegóły: {e.to_dict()}")


async def test_configuration():
    """Test konfiguracji"""
    print("\n=== Test konfiguracji ===")

    print(f"APP_NAME: {settings.APP_NAME}")
    print(f"APP_VERSION: {settings.APP_VERSION}")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
    print(f"LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"OLLAMA_URL: {settings.OLLAMA_URL}")
    print(f"OLLAMA_MODEL: {settings.OLLAMA_MODEL}")
    print(f"DEFAULT_CODE_MODEL: {settings.DEFAULT_CODE_MODEL}")
    print(f"USE_MMLW_EMBEDDINGS: {settings.USE_MMLW_EMBEDDINGS}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")

    # Sprawdź klucze API
    api_keys = [
        "LLM_API_KEY",
        "OPENWEATHER_API_KEY",
        "PERPLEXITY_API_KEY",
        "WEATHER_API_KEY",
    ]

    print("\nStatus kluczy API:")
    for key in api_keys:
        value = getattr(settings, key, "")
        status = "✅ Ustawiony" if value else "❌ Brak"
        print(f"{key}: {status}")


async def main():
    """Główna funkcja testowa"""
    print("🧪 Rozpoczynam testy napraw systemu FoodSave AI")
    print("=" * 50)

    try:
        # Test konfiguracji
        await test_configuration()

        # Test modeli językowych
        await test_llm_models()

        # Test API Perplexity
        await test_perplexity_api()

        # Test agentów
        await test_search_agent()
        await test_weather_agent()

        # Test obsługi wyjątków
        await test_exception_handling()

        print("\n" + "=" * 50)
        print("✅ Wszystkie testy zakończone")

    except Exception as e:
        print(f"\n❌ Błąd podczas testów: {e}")
        logger.exception("Błąd podczas testów")


if __name__ == "__main__":
    asyncio.run(main())
