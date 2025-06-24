import logging
from typing import Dict, Tuple

try:
    from langdetect import LangDetectException, detect_langs

    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
    logging.warning(
        "langdetect not installed. Language detection will not work properly."
    )

logger = logging.getLogger(__name__)

# Mapy do konwersji między formatami kodów języków
ISO_639_TO_LANGDETECT = {
    "pl": "pl",
    "en": "en",
    "de": "de",
    "fr": "fr",
    "ru": "ru",
    "es": "es",
    "it": "it",
    "cs": "cs",
    "sk": "sk",
    "uk": "uk",
}

LANGDETECT_TO_ISO_639 = {v: k for k, v in ISO_639_TO_LANGDETECT.items()}


class LanguageDetector:
    """
    Klasa do wykrywania języka tekstu.
    Wykorzystuje bibliotekę langdetect z fallbackiem do prostej heurystyki.
    """

    def __init__(self) -> None:
        self.available = LANGDETECT_AVAILABLE

        # Mapowanie słów kluczowych dla różnych języków
        self.language_keywords = {
            "pl": [
                "jest",
                "nie",
                "tak",
                "co",
                "jak",
                "dla",
                "gdzie",
                "kiedy",
                "dlaczego",
                "który",
                "wszystko",
                "cześć",
                "dziękuję",
                "proszę",
                "przepraszam",
                "dobrze",
                "źle",
                "bardzo",
                "trochę",
                "dużo",
            ],
            "en": [
                "is",
                "not",
                "yes",
                "what",
                "how",
                "for",
                "where",
                "when",
                "why",
                "which",
                "all",
                "hello",
                "thank",
                "please",
                "sorry",
                "good",
                "bad",
                "very",
                "little",
                "much",
            ],
            "de": [
                "ist",
                "nicht",
                "ja",
                "was",
                "wie",
                "für",
                "wo",
                "wann",
                "warum",
                "welche",
                "alles",
                "hallo",
                "danke",
                "bitte",
                "entschuldigung",
                "gut",
                "schlecht",
                "sehr",
                "wenig",
                "viel",
            ],
        }

        if not self.available:
            logger.warning("LanguageDetector initialized without langdetect library")

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Wykrywa język tekstu i zwraca kod ISO 639-1 oraz pewność detekcji.

        Args:
            text: Tekst do analizy

        Returns:
            Tuple[str, float]: (kod_języka, pewność)
        """
        if not text or len(text.strip()) < 3:
            return "en", 0.5  # Default for very short texts

        # Metoda preferowana - langdetect
        if self.available:
            try:
                # Próba wykrycia języka z pewnością
                lang_probabilities = detect_langs(text)
                if lang_probabilities:
                    detected_lang = lang_probabilities[0].lang
                    confidence = lang_probabilities[0].prob

                    # Mapowanie do ISO 639-1
                    if detected_lang in LANGDETECT_TO_ISO_639:
                        return LANGDETECT_TO_ISO_639[detected_lang], confidence
                    return detected_lang, confidence

            except LangDetectException as e:
                logger.warning(f"Language detection error: {e}")

        # Fallback do heurystyki słów kluczowych
        return self._keyword_based_detection(text)

    def _keyword_based_detection(self, text: str) -> Tuple[str, float]:
        """
        Wykrywa język na podstawie słów kluczowych.

        Args:
            text: Tekst do analizy

        Returns:
            Tuple[str, float]: (kod_języka, pewność)
        """
        text_lower = text.lower()
        words = set(text_lower.split())

        # Liczenie wystąpień słów kluczowych dla każdego języka
        scores: Dict[str, int] = {lang: 0 for lang in self.language_keywords}

        for lang, keywords in self.language_keywords.items():
            for keyword in keywords:
                if keyword in words or keyword in text_lower:
                    scores[lang] += 1

        # Wybór języka z największym wynikiem
        if not scores:
            return "en", 0.5  # Default

        best_lang = max(scores, key=lambda k: scores[k])

        # Obliczanie pewności (max 0.9 dla tej metody)
        total_keywords = sum(
            len(keywords) for keywords in self.language_keywords.values()
        )
        confidence = min(
            0.9,
            scores[best_lang] / (total_keywords / len(self.language_keywords)) * 0.9,
        )

        return best_lang, confidence

    def is_polish(self, text: str) -> bool:
        """
        Sprawdza, czy tekst jest w języku polskim.

        Args:
            text: Tekst do analizy

        Returns:
            bool: True jeśli język to polski, False w przeciwnym wypadku
        """
        lang, _ = self.detect_language(text)
        return lang == "pl"


# Singleton instance
language_detector = LanguageDetector()
