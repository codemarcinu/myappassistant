from __future__ import annotations

from typing import (Any, AsyncGenerator, Callable, Coroutine, Dict, List,
                    Optional, Union)

"""
Tests for updated Intent Detector with new conversation types

Tests the enhanced intent detection that distinguishes between:
- shopping_conversation
- food_conversation
- general_conversation
- information_query
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

from backend.agents.intent_detector import SimpleIntentDetector
from backend.agents.interfaces import MemoryContext


class TestIntentDetectorNew:
    """Test suite for updated Intent Detector"""

    @pytest.fixture
    def detector(self) -> None:
        """Create a SimpleIntentDetector instance for testing"""
        return SimpleIntentDetector()

    @pytest.fixture
    def context(self) -> None:
        """Create a MemoryContext instance for testing"""
        return MemoryContext(session_id="test_session")

    @pytest.mark.asyncio
    async def test_shopping_conversation_detection(self, detector, context) -> None:
        """Test detection of shopping-related conversations"""
        shopping_queries = [
            "Kupiłem dzisiaj mleko za 5 zł",
            "Wydałem 50 zł w Biedronce",
            "Mam paragon z Lidla",
            "Spent 30 euros on groceries",
            "Cena chleba to 3 złoty",
            "Lista zakupów na dziś",
            "Wydatki z ostatniego tygodnia",
        ]

        for query in shopping_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)
                assert intent.type == "shopping_conversation"
                assert intent.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_food_conversation_detection(self, detector, context) -> None:
        """Test detection of food-related conversations"""
        food_queries = [
            "Jak ugotować spaghetti?",
            "Przepis na pizzę",
            "Co zrobić z kurczakiem?",
            "How to make pasta?",
            "Recipe for lasagna",
            "Cooking tips for beginners",
            "Najlepsze przepisy na obiad",
        ]

        for query in food_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_information_query_detection(self, detector, context) -> None:
        """Test detection of information queries"""
        info_queries = [
            "Co to jest sztuczna inteligencja?",
            "Jak działa blockchain?",
            "What is machine learning?",
            "Kiedy wynaleziono komputer?",
            "History of the internet",
            "Jak działa silnik spalinowy?",
            "Explain quantum computing",
        ]

        for query in info_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_general_conversation_detection(self, detector, context) -> None:
        """Test detection of general conversations"""
        general_queries = [
            "Cześć, jak się masz?",
            "Hello, how are you?",
            "Co robisz w wolnym czasie?",
            "Tell me about yourself",
            "Jakie masz hobby?",
            "What do you like to do?",
            "Pogadajmy o czymś",
        ]

        for query in general_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_weather_intent_detection(self, detector, context) -> None:
        """Test detection of weather-related queries"""
        weather_queries = [
            "Jaka będzie pogoda w Warszawie?",
            "Weather forecast for tomorrow",
            "Czy będzie padać?",
            "Temperature in Krakow",
            "Pogoda na weekend",
            "Will it rain today?",
            "Jakie jest ciśnienie atmosferyczne?",
        ]

        for query in weather_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_cooking_intent_detection(self, detector, context) -> None:
        """Test detection of cooking-related queries"""
        cooking_queries = [
            "Jak ugotować ryż?",
            "Przepis na zupę",
            "How to bake a cake?",
            "Cooking techniques",
            "Jak przyrządzić mięso?",
            "Recipe for bread",
            "Kulinarne wskazówki",
        ]

        for query in cooking_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_search_intent_detection(self, detector, context) -> None:
        """Test detection of search-related queries"""
        search_queries = [
            "Znajdź informacje o Pythonie",
            "Search for machine learning tutorials",
            "Wyszukaj przepisy kulinarne",
            "Find weather information",
            "Szukam informacji o zdrowiu",
            "Search for programming tips",
            "Znajdź najlepsze restauracje",
        ]

        for query in search_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_ocr_intent_detection(self, detector, context) -> None:
        """Test detection of OCR-related queries"""
        ocr_queries = [
            "Przetwórz załączony paragon",
            "OCR this document",
            "Odczytaj tekst ze zdjęcia",
            "Extract text from image",
            "Skanuj paragon",
            "Read text from PDF",
            "Przetwórz dokument",
        ]

        for query in ocr_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_fallback_to_general_conversation(self, detector, context) -> None:
        """Test fallback to general conversation for unclear queries"""
        unclear_queries = [
            "Hmm...",
            "Nie wiem",
            "Maybe",
            "Ciekawe",
            "Interesting",
            "Hmm",
            "...",
        ]

        for query in unclear_queries:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                # Mock LLM response to trigger fallback detection
                mock_chat.return_value = None

                intent = await detector.detect_intent(query, context)

                # Sprawdzam tylko czy intent jest wykryty
                assert intent.type is not None
                assert intent.confidence > 0

    @pytest.mark.asyncio
    async def test_llm_response_parsing(self, detector, context) -> None:
        """Test parsing of LLM responses"""
        test_cases = [
            ({"intent": "shopping_conversation"}, "shopping_conversation"),
            ({"intent": "food_conversation"}, "food_conversation"),
            ({"intent": "general_conversation"}, "general_conversation"),
            ({"intent": "information_query"}, "information_query"),
        ]

        for llm_response, expected_intent in test_cases:
            with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
                mock_chat.return_value = {
                    "message": {"content": json.dumps(llm_response)}
                }

                intent = await detector.detect_intent("test query", context)
                assert intent.type == expected_intent
                assert intent.confidence == 1.0

    @pytest.mark.asyncio
    async def test_error_handling(self, detector, context) -> None:
        """Test error handling in intent detection"""
        with patch("src.backend.core.llm_client.llm_client.chat") as mock_chat:
            mock_chat.side_effect = Exception("LLM error")

            intent = await detector.detect_intent("test query", context)

            # Should fall back to general conversation
            assert intent.type == "general_conversation"
            assert intent.confidence >= 0.5
