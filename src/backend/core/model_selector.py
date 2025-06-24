import logging
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from backend.core.language_detector import language_detector

logger = logging.getLogger(__name__)


class ModelTask(str, Enum):
    """Typy zadań dla modeli AI"""

    TEXT_ONLY = "text_only"
    IMAGE_ANALYSIS = "image_analysis"
    CODE_GENERATION = "code_generation"
    CREATIVE = "creative"
    RAG = "rag"  # Retrieval Augmented Generation
    STRUCTURED_OUTPUT = "structured_output"


class ModelCapability(TypedDict):
    languages: Dict[str, float]
    tasks: Dict[ModelTask, float]
    context_length: int


class ModelSelector:
    """
    Klasa odpowiedzialna za inteligentny wybór modelu językowego
    w zależności od zadania, języka i złożoności.

    Implementuje logikę:
    - Bielik dla zapytań w języku polskim
    - Gemma dla zapytań w innych językach
    - Gemma dla zadań multimodalnych (analiza obrazów)
    - Gemma dla bardzo złożonych zadań
    """

    # Modele domyślne
    DEFAULT_POLISH_MODEL = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
    DEFAULT_INTERNATIONAL_MODEL = "gemma3:12b"

    # Moce przetwarzania poszczególnych modeli (arbitralne wartości)
    MODEL_CAPABILITIES: Dict[str, ModelCapability] = {
        "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0": {
            "languages": {"pl": 0.95, "en": 0.75},
            "tasks": {
                ModelTask.TEXT_ONLY: 0.9,
                ModelTask.CODE_GENERATION: 0.7,
                ModelTask.CREATIVE: 0.8,
                ModelTask.RAG: 0.8,
                ModelTask.STRUCTURED_OUTPUT: 0.7,
                ModelTask.IMAGE_ANALYSIS: 0.0,  # Nie obsługuje obrazów
            },
            "context_length": 32000,
        },
        "gemma3:12b": {
            "languages": {"pl": 0.8, "en": 0.95, "de": 0.9, "fr": 0.9, "es": 0.9},
            "tasks": {
                ModelTask.TEXT_ONLY: 0.95,
                ModelTask.CODE_GENERATION: 0.9,
                ModelTask.CREATIVE: 0.9,
                ModelTask.RAG: 0.95,
                ModelTask.STRUCTURED_OUTPUT: 0.9,
                ModelTask.IMAGE_ANALYSIS: 0.95,  # Obsługuje obrazy
            },
            "context_length": 128000,
        },
    }

    DEFAULT_CAPABILITY: ModelCapability = {
        "languages": {},
        "tasks": {},
        "context_length": 0,
    }

    def __init__(self) -> None:
        """Inicjalizacja selektora modeli"""
        self.language_detector = language_detector
        logger.info("ModelSelector initialized")

    def select_model(
        self,
        query: str,
        task: ModelTask = ModelTask.TEXT_ONLY,
        complexity: float = 0.5,
        contains_images: bool = False,
        context_length: int = 0,
        available_models: Optional[List[str]] = None,
    ) -> str:
        """
        Wybiera najlepszy model dla danego zapytania i zadania.

        Args:
            query: Tekst zapytania
            task: Typ zadania do wykonania
            complexity: Złożoność zadania (0.0-1.0)
            contains_images: Czy zapytanie zawiera obrazy
            context_length: Szacowana długość kontekstu
            available_models: Lista dostępnych modeli (opcjonalnie)

        Returns:
            str: Nazwa najlepszego modelu
        """
        # Domyślna lista modeli
        if available_models is None:
            available_models = list(self.MODEL_CAPABILITIES.keys())

        # Wykryj język zapytania
        detected_language, language_confidence = self.language_detector.detect_language(
            query
        )
        logger.info(
            f"Detected language: {detected_language} (confidence: {language_confidence:.2f})"
        )

        # Przesiej modele pod kątem wymagań
        candidate_models = available_models.copy()

        # Jeśli zapytanie zawiera obrazy, wymaga modelu multimodalnego
        if contains_images:
            candidate_models = [
                model
                for model in candidate_models
                if self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                    "tasks"
                ].get(ModelTask.IMAGE_ANALYSIS, 0)
                > 0
            ]
            logger.info(f"Filtered to multimodal models: {candidate_models}")

            # Jeśli nie ma dostępnych modeli multimodalnych
            if not candidate_models:
                logger.warning("No multimodal models available, falling back to Gemma")
                return self.DEFAULT_INTERNATIONAL_MODEL

        # Jeśli kontekst jest duży, potrzebujemy modelu z dużym kontekstem
        if context_length > 0:
            candidate_models = [
                model
                for model in candidate_models
                if self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                    "context_length"
                ]
                >= context_length
            ]
            logger.info(f"Filtered to large context models: {candidate_models}")

            # Jeśli nie ma modeli z wystarczającym kontekstem
            if not candidate_models:
                logger.warning(
                    f"No models with sufficient context length ({context_length}), "
                    + f"selecting model with largest context"
                )
                return max(
                    available_models,
                    key=lambda m: self.MODEL_CAPABILITIES.get(
                        m, self.DEFAULT_CAPABILITY
                    )["context_length"],
                )

        # Wartości do oceny modeli
        model_scores: Dict[str, float] = {}

        for model in candidate_models:
            # Dodaj punkty za dopasowanie językowe
            language_score = self.MODEL_CAPABILITIES.get(
                model, self.DEFAULT_CAPABILITY
            )["languages"].get(detected_language, 0.5)

            # Dodaj punkty za obsługę zadania
            task_score = self.MODEL_CAPABILITIES.get(model, self.DEFAULT_CAPABILITY)[
                "tasks"
            ].get(task, 0.5)

            # Wynik końcowy - ważona suma
            if detected_language == "pl":
                # Dla polskich zapytań język ma większe znaczenie
                final_score = 0.6 * language_score + 0.4 * task_score
            else:
                # Dla innych języków zadanie ma większe znaczenie
                final_score = 0.4 * language_score + 0.6 * task_score

            # Dla bardzo złożonych zadań preferuj zawsze Gemmę
            if complexity > 0.8:
                if model == self.DEFAULT_INTERNATIONAL_MODEL:
                    final_score += 0.2

            model_scores[model] = final_score

        # Wybierz model z najwyższym wynikiem
        if model_scores:
            best_model = max(model_scores.items(), key=lambda x: x[1])[0]
            logger.info(
                f"Selected model {best_model} with score {model_scores[best_model]:.2f} (lang: {detected_language}, task: {task}, complexity: {complexity:.2f})"
            )
            return best_model

        # Fallback - dla polskiego Bielik, dla innych Gemma
        if detected_language == "pl":
            logger.info(
                "No suitable models found, falling back to default Polish model"
            )
            return self.DEFAULT_POLISH_MODEL
        else:
            logger.info(
                "No suitable models found, falling back to default international model"
            )
            return self.DEFAULT_INTERNATIONAL_MODEL

    def is_multimodal_task(self, task: ModelTask) -> bool:
        """Sprawdza, czy zadanie wymaga modelu multimodalnego"""
        return task in [ModelTask.IMAGE_ANALYSIS]

    def is_complex_task(self, task: ModelTask) -> bool:
        """Sprawdza, czy zadanie jest złożone"""
        return task in [
            ModelTask.CODE_GENERATION,
            ModelTask.RAG,
            ModelTask.STRUCTURED_OUTPUT,
        ]


# Singleton instance
model_selector = ModelSelector()
