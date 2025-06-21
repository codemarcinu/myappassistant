import logging
import os
from typing import Any, Dict, List, Optional

# Set User-Agent for transformers library
os.environ.setdefault(
    "USER_AGENT", "FoodSave-AI/1.0.0 (https://github.com/foodsave-ai)"
)

import torch
from transformers import AutoTokenizer, pipeline

from .orchestration_components import IntentData, MemoryContext  # Importuj klasy bazowe

logger = logging.getLogger(__name__)


class BERTIntentDetector:
    def __init__(
        self,
        model_name: str = "distilbert-base-uncased",
        labels: Optional[List[str]] = None,
    ):
        self.model_name = model_name
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.classifier = None
        # Przykładowe etykiety intencji. W prawdziwej aplikacji pochodziłyby z danych treningowych.
        self.intent_labels = (
            labels
            if labels is not None
            else [
                "cooking",
                "weather",
                "search",
                "document",
                "shopping",
                "meal_plan",
                "analytics",
                "general",
            ]
        )
        self._is_initialized = False

    async def initialize(self):
        """Inicjalizuje model i klasyfikator."""
        if self._is_initialized:
            return

        try:
            # Określenie device'u (CPU/GPU)
            device = 0 if torch.cuda.is_available() else -1
            logger.info(
                f"Initializing BERTIntentDetector on device: {device if device != -1 else 'cpu'}"
            )

            # Tworzenie pipeline do klasyfikacji tekstu
            # Należy pamiętać, że do klasyfikacji customowych intencji
            # potrzebny jest fine-tuning modelu na własnym zbiorze danych.
            # Ten pipeline działa na pre-trainowanym modelu i jego oryginalnych etykietach,
            # więc _map_predictions_to_intents jest kluczowe.
            self.classifier = pipeline(
                "text-classification",
                model=self.model_name,
                tokenizer=self.tokenizer,
                device=device,
                return_all_scores=True,  # Ważne dla uzyskania wszystkich prawdopodobieństw
            )
            self._is_initialized = True
            logger.info("BERTIntentDetector initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize BERTIntentDetector: {e}", exc_info=True)
            self.classifier = None  # Zresetuj, jeśli inicjalizacja się nie powiodła
            raise

    async def detect_intent(self, text: str, context: MemoryContext) -> IntentData:
        """Wykrywa intencję przy użyciu klasyfikacji opartej na BERT."""
        if not self._is_initialized:
            await self.initialize()
            if not self._is_initialized:  # Ponowna weryfikacja po próbie inicjalizacji
                logger.error(
                    "BERTIntentDetector not initialized, falling back to simple detection."
                )
                return self._fallback_detection_simple(text)

        processed_text = self._preprocess_text(text, context)

        try:
            predictions = self.classifier(processed_text)[
                0
            ]  # pipeline zwraca listę list, bierzemy pierwszy wynik

            intent_scores = self._map_predictions_to_intents(predictions)

            # Znajdź intencję z najwyższym wynikiem
            best_intent_type = "general"
            max_confidence = 0.0

            for intent, score in intent_scores.items():
                if score > max_confidence:
                    max_confidence = score
                    best_intent_type = intent

            # W przypadku niskiej pewności, można użyć fallbacku
            if max_confidence < 0.5:  # Próg pewności
                logger.warning(
                    f"Low confidence for intent '{best_intent_type}' ({max_confidence:.2f}), falling back."
                )
                return self._fallback_detection_simple(text)

            # TODO: Dodaj ekstrakcję encji, jeśli model BERT jest przystosowany do NER
            entities = {}

            return IntentData(
                type=best_intent_type,
                entities=entities,
                confidence=max_confidence,
                all_scores=intent_scores,  # Opcjonalnie, dla debugowania
            )

        except Exception as e:
            logger.error(
                f"Error during BERT intent detection: {e}. Falling back to simple detection.",
                exc_info=True,
            )
            return self._fallback_detection_simple(text)

    def _preprocess_text(self, text: str, context: MemoryContext) -> str:
        """Przygotowuje tekst, dodając kontekst rozmowy, jeśli dostępny."""
        history_messages = [
            msg["content"] for msg in context.history if "content" in msg
        ]
        if history_messages:
            # Użyj np. 3 ostatnich wiadomości jako kontekst
            context_str = " ".join(history_messages[-3:])
            return f"{context_str} [SEP] {text}"
        return text

    def _map_predictions_to_intents(
        self, predictions: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Mapuje predykcje modelu BERT do zdefiniowanych etykiet intencji."""
        # Wymaga dostosowania do konkretnego pre-trainowanego modelu BERT i jego oryginalnych etykiet.
        # Jest to uproszczenie; idealnie, model byłby fine-tunowany na dokładnie tych etykietach.
        intent_scores = {label: 0.0 for label in self.intent_labels}

        for pred in predictions:
            label = pred["label"].lower()
            score = pred["score"]

            # Przykładowe mapowanie: dostosuj do swojego modelu i intencji
            if "cook" in label or "recipe" in label or "food" in label:
                intent_scores["cooking"] += score
            elif "weather" in label or "climate" in label or "forecast" in label:
                intent_scores["weather"] += score
            elif "search" in label or "find" in label or "lookup" in label:
                intent_scores["search"] += score
            elif "document" in label or "read" in label or "rag" in label:
                intent_scores["document"] += score
            elif "shop" in label or "buy" in label or "product" in label:
                intent_scores["shopping"] += score
            elif "plan" in label or "meal" in label or "diet" in label:
                intent_scores["meal_plan"] += score
            elif "analytic" in label or "data" in label or "report" in label:
                intent_scores["analytics"] += score
            else:
                intent_scores["general"] += score

        # Normalizacja wyników, jeśli są sumowane
        total_score = sum(intent_scores.values())
        if total_score > 0:
            return {k: v / total_score for k, v in intent_scores.items()}
        return intent_scores

    def _fallback_detection_simple(self, text: str) -> IntentData:
        """Prosty fallback detektor intencji."""
        text_lower = text.lower()
        if "pogoda" in text_lower or "temperatura" in text_lower:
            return IntentData("weather", {"location": "unknown"}, 0.7)
        if "przepis" in text_lower or "gotować" in text_lower:
            return IntentData("cooking", {}, 0.7)
        if "szukaj" in text_lower or "znajdź" in text_lower:
            return IntentData("search", {}, 0.7)
        if "dokument" in text_lower or "przeczytaj" in text_lower:
            return IntentData("document", {}, 0.7)
        return IntentData("general", {}, 0.5)
