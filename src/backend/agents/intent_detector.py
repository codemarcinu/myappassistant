from __future__ import annotations

import json
import logging

import httpx

from backend.agents.interfaces import IntentData, MemoryContext
from backend.core.hybrid_llm_client import hybrid_llm_client
from backend.core.utils import extract_json_from_text

logger = logging.getLogger(__name__)


class SimpleIntentDetector:
    def __init__(self) -> None:
        self.ollama_available = self._check_ollama_availability()

    def _check_ollama_availability(self) -> bool:
        """Check if Ollama server is available via HTTP"""
        try:
            # Try to connect to Ollama server via HTTP
            response = httpx.get("http://ollama:11434/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ollama server not available: {e}")
            return False

    async def detect_intent(self, text: str, context: MemoryContext) -> IntentData:
        """
        Detektor intencji oparty o LLM.
        """
        try:
            logger.info(f"Detecting intent for text: '{text}'")

            # Check if Ollama is available
            if not self.ollama_available:
                logger.warning(
                    "Ollama server not available, using fallback intent detection"
                )
                fallback_intent = self._fallback_intent_detection(text)
                logger.info(f"Fallback intent detected: {fallback_intent.type}")
                return fallback_intent

            prompt = f"Wykryj intencję użytkownika na podstawie tekstu: '{text}'. Zwróć JSON: {{\"intent\": ...}}"
            messages = [
                {
                    "role": "system",
                    "content": "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON.",
                },
                {"role": "user", "content": prompt},
            ]

            logger.debug(f"Sending intent detection request for text: {text}")
            response = await hybrid_llm_client.chat(
                model="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                messages=messages,
                stream=False,
                options={"temperature": 0.0},
            )

            logger.debug(f"LLM response: {response}")

            intent_type = "general"
            if response and "message" in response:
                try:
                    content = response["message"]["content"]
                    logger.info(f"LLM content: {content}")

                    # Use extract_json_from_text to handle markdown and other formats
                    json_str = extract_json_from_text(content)
                    if json_str:
                        parsed = json.loads(json_str)
                        intent_type = parsed.get("intent", "general")
                        logger.info(f"Successfully parsed intent: {intent_type}")
                    else:
                        logger.warning(f"No valid JSON found in content: {content}")
                        intent_type = self._fallback_intent_detection(text).type

                except Exception as e:
                    logger.warning(f"Failed to parse LLM response: {e}")
                    logger.debug(f"Raw content: {content}")
                    intent_type = self._fallback_intent_detection(text).type
            else:
                logger.warning(f"Invalid LLM response format: {response}")
                intent_type = self._fallback_intent_detection(text).type

            logger.info(f"Final intent detected: {intent_type}")
            return IntentData(type=intent_type, entities={}, confidence=1.0)

        except Exception as e:
            logger.error(f"Error in intent detection: {e}")
            # Return fallback intent on error
            fallback_intent = self._fallback_intent_detection(text)
            logger.info(f"Using fallback intent: {fallback_intent.type}")
            return fallback_intent

    def _fallback_intent_detection(self, text: str) -> IntentData:
        """Simple rule-based intent detection as fallback"""
        text_lower = text.lower()
        logger.info(f"Using fallback intent detection for text: '{text}'")

        # General conversation detection
        general_keywords = [
            "cześć",
            "witaj",
            "dzień dobry",
            "dobry wieczór",
            "hej",
            "siema",
            "dzięki",
            "dziękuję",
            "dziękuję bardzo",
            "jak się masz",
            "co słychać",
            "co u ciebie",
            "ok",
            "rozumiem",
            "jasne",
            "dobra",
            "pomoc",
            "pomóż",
            "help",
            "kto ty jesteś",
            "kim jesteś",
            "żart",
            "opowiedz żart",
            "powiedź coś śmiesznego",
        ]
        if any(keyword in text_lower for keyword in general_keywords):
            logger.info(f"General conversation intent detected for text: '{text}'")
            return IntentData(type="general_conversation", entities={}, confidence=0.95)

        # Shopping conversation detection - expanded keywords
        shopping_keywords = [
            "zakupy",
            "shopping",
            "paragon",
            "receipt",
            "wydałem",
            "spent",
            "kupiłem",
            "bought",
            "cena",
            "price",
            "koszt",
            "cost",
            "sklep",
            "store",
            "market",
            "biedronka",
            "lidl",
            "żabka",
            "carrefour",
            "tesco",
            "suma",
            "total",
            "kwota",
            "amount",
            "produkt",
            "product",
            "lista zakupów",
            "shopping list",
            "wydatki",
            "expenses",
            "budżet",
            "budget",
            "oszczędności",
            "savings",
            "promocja",
            "discount",
            "rabat",
            "sale",
        ]
        if any(keyword in text_lower for keyword in shopping_keywords):
            logger.info(f"Shopping conversation intent detected for text: '{text}'")
            return IntentData(type="shopping_conversation", entities={}, confidence=0.9)

        # Categorization detection - check before food conversation
        categorization_keywords = [
            "kategoryzuj",
            "categorize",
            "klasyfikuj",
            "classify",
            "kategoria",
            "category",
            "grupuj",
            "group",
            "sortuj",
            "sort",
            "organizuj",
            "organize",
            "przypisz kategorię",
            "assign category",
            "jaką kategorię",
            "what category",
        ]
        if any(keyword in text_lower for keyword in categorization_keywords):
            logger.info(f"Categorization intent detected for text: '{text}'")
            return IntentData(type="categorization", entities={}, confidence=0.8)

        # Food conversation detection - expanded keywords
        food_keywords = [
            "jedzenie",
            "food",
            "przepis",
            "recipe",
            "gotowanie",
            "cooking",
            "kuchnia",
            "kitchen",
            "posiłek",
            "meal",
            "obiad",
            "dinner",
            "śniadanie",
            "breakfast",
            "kolacja",
            "supper",
            "składniki",
            "ingredients",
            "smak",
            "taste",
            "smaczne",
            "delicious",
            "ugotować",
            "cook",
            "piec",
            "bake",
            "smażyć",
            "fry",
            "gotować",
            "boil",
            "warzywa",
            "vegetables",
            "owoce",
            "fruits",
            "mięso",
            "meat",
            "ryba",
            "fish",
            "mleko",
            "milk",
            "chleb",
            "bread",
            "ser",
            "cheese",
            "jajka",
            "eggs",
            "makaron",
            "pasta",
            "ryż",
            "rice",
            "ziemniaki",
            "potatoes",
        ]
        if any(keyword in text_lower for keyword in food_keywords):
            logger.info(f"Food conversation intent detected for text: '{text}'")
            return IntentData(type="food_conversation", entities={}, confidence=0.8)

        # Information query detection - keywords indicating need for external information
        info_keywords = [
            "co to jest",
            "what is",
            "kto to",
            "who is",
            "gdzie",
            "where",
            "kiedy",
            "when",
            "dlaczego",
            "why",
            "jak",
            "how",
            "informacje",
            "information",
            "dane",
            "data",
            "statystyki",
            "statistics",
            "historia",
            "history",
            "nauka",
            "science",
            "technologia",
            "technology",
            "aktualności",
            "news",
            "wydarzenia",
            "events",
            "fakty",
            "facts",
            "prawda",
            "truth",
        ]
        if any(keyword in text_lower for keyword in info_keywords):
            logger.info(f"Information query intent detected for text: '{text}'")
            return IntentData(type="information_query", entities={}, confidence=0.8)

        # Weather detection - expanded keywords
        weather_keywords = [
            "weather",
            "pogoda",
            "temperature",
            "temperatura",
            "jaka pogoda",
            "prognoza",
            "forecast",
            "deszcz",
            "rain",
            "śnieg",
            "snow",
            "słońce",
            "sun",
            "wiatr",
            "wind",
            "wilgotność",
            "humidity",
            "stopnie",
            "degrees",
            "ciepło",
            "cold",
            "zimno",
            "hot",
        ]
        if any(keyword in text_lower for keyword in weather_keywords):
            logger.info(f"Weather intent detected for text: '{text}'")
            return IntentData(type="weather", entities={}, confidence=0.8)

        # Cooking detection
        cooking_keywords = [
            "cook",
            "recipe",
            "gotuj",
            "przepis",
            "kuchnia",
            "jedzenie",
            "food",
            "meal",
            "posiłek",
            "obiad",
            "dinner",
            "śniadanie",
            "breakfast",
            "kolacja",
            "supper",
            "składniki",
            "ingredients",
        ]
        if any(keyword in text_lower for keyword in cooking_keywords):
            logger.info(f"Cooking intent detected for text: '{text}'")
            return IntentData(type="cooking", entities={}, confidence=0.8)

        # Search detection
        search_keywords = [
            "search",
            "find",
            "szukaj",
            "znajdź",
            "informacje",
            "information",
            "co to jest",
            "what is",
            "kto to",
            "who is",
            "gdzie",
            "where",
        ]
        if any(keyword in text_lower for keyword in search_keywords):
            logger.info(f"Search intent detected for text: '{text}'")
            return IntentData(type="search", entities={}, confidence=0.8)

        # RAG/document detection
        rag_keywords = [
            "document",
            "file",
            "dokument",
            "plik",
            "pdf",
            "text",
            "tekst",
            "analizuj",
            "analyze",
            "przeczytaj",
            "read",
        ]
        if any(keyword in text_lower for keyword in rag_keywords):
            logger.info(f"RAG intent detected for text: '{text}'")
            return IntentData(type="rag", entities={}, confidence=0.8)

        # OCR/image detection
        ocr_keywords = [
            "image",
            "photo",
            "zdjęcie",
            "obraz",
            "picture",
            "paragon",
            "receipt",
            "scan",
            "skanuj",
            "ocr",
        ]
        if any(keyword in text_lower for keyword in ocr_keywords):
            logger.info(f"OCR intent detected for text: '{text}'")
            return IntentData(type="ocr", entities={}, confidence=0.8)

        # Greeting detection
        greeting_keywords = [
            "cześć",
            "hello",
            "hi",
            "witam",
            "dzień dobry",
            "good morning",
            "good afternoon",
            "good evening",
            "hej",
            "hey",
        ]
        if any(keyword in text_lower for keyword in greeting_keywords):
            logger.info(f"General conversation intent detected for text: '{text}'")
            return IntentData(type="general_conversation", entities={}, confidence=0.7)

        # Default to general conversation if no other intent is detected
        logger.info(
            f"No specific intent detected, defaulting to general conversation for text: '{text}'"
        )
        return IntentData(type="general_conversation", entities={}, confidence=0.5)
