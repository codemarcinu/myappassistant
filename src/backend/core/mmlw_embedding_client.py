"""
MMLW Embedding Client - specjalizowany klient dla polskiego modelu embeddingów
"""

import asyncio
import logging
from typing import Any, Dict, List

try:
    import torch
    from transformers import AutoModel, AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers not available. MMLW embeddings will not work.")

logger = logging.getLogger(__name__)


class MMLWEmbeddingClient:
    """
    Klient do obsługi modelu MMLW (sdadas/mmlw-retrieval-roberta-base)
    Specjalizowany dla języka polskiego i zadań wyszukiwania informacji
    """

    def __init__(self, model_name: str = "sdadas/mmlw-retrieval-roberta-base") -> None:
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = None
        self.is_initialized = False
        self._initialization_lock = asyncio.Lock()
        self._initialization_task = None

    async def _ensure_initialized(self) -> None:
        """Zapewnia, że model jest zainicjalizowany (lazy loading)"""
        if self.is_initialized:
            return True

        # Jeśli inicjalizacja już trwa, poczekaj na jej zakończenie
        if self._initialization_task and not self._initialization_task.done():
            await self._initialization_task
            return self.is_initialized

        # Rozpocznij inicjalizację
        async with self._initialization_lock:
            if self.is_initialized:  # Sprawdź ponownie po uzyskaniu locka
                return True

            self._initialization_task = asyncio.create_task(self._initialize_model())
            await self._initialization_task
            return self.is_initialized

    async def _initialize_model(self) -> None:
        """Wewnętrzna metoda inicjalizacji modelu"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("Transformers not available. Cannot initialize MMLW.")
            return False

        try:
            logger.info(f"Initializing MMLW model: {self.model_name}")

            # Sprawdź dostępność CUDA
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("Using CUDA for MMLW embeddings")
            else:
                self.device = torch.device("cpu")
                logger.info("Using CPU for MMLW embeddings")

            # Załaduj tokenizer i model
            logger.info("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

            logger.info("Loading model...")
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()

            self.is_initialized = True
            logger.info("MMLW model initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize MMLW model: {e}")
            self.is_initialized = False
            return False

    async def initialize(self) -> None:
        """Inicjalizacja modelu MMLW (deprecated - użyj _ensure_initialized)"""
        return await self._ensure_initialized()

    async def embed_text(self, text: str) -> List[float]:
        """
        Generuje embedding dla tekstu używając modelu MMLW

        Args:
            text: Tekst do przetworzenia

        Returns:
            Lista floatów reprezentująca embedding (768 wymiarów)
        """
        # Lazy loading - zainicjalizuj model jeśli potrzebny
        if not await self._ensure_initialized() or not self.tokenizer or not self.model:
            logger.error("MMLW model not initialized or tokenizer/model is None")
            return []

        try:
            # Tokenizacja tekstu
            inputs = self.tokenizer(
                text, return_tensors="pt", max_length=512, truncation=True, padding=True
            )

            # Przenieś na odpowiednie urządzenie
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generuj embedding
            with torch.no_grad():
                outputs = self.model(**inputs)
                # Użyj [CLS] token jako reprezentację całego tekstu
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            return embedding[0].tolist()

        except Exception as e:
            logger.error(f"Error generating MMLW embedding: {e}")
            return []

    async def embed_batch(
        self, texts: List[str], batch_size: int = 8
    ) -> List[List[float]]:
        """
        Generuje embeddingi dla listy tekstów

        Args:
            texts: Lista tekstów do przetworzenia
            batch_size: Rozmiar batcha

        Returns:
            Lista list floatów reprezentujących embeddingi
        """
        # Lazy loading - zainicjalizuj model jeśli potrzebny
        if not await self._ensure_initialized() or not self.tokenizer or not self.model:
            logger.error("MMLW model not initialized or tokenizer/model is None")
            return [[] for _ in texts]

        embeddings = []

        try:
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i : i + batch_size]

                # Tokenizacja batcha
                inputs = self.tokenizer(
                    batch_texts,
                    return_tensors="pt",
                    max_length=512,
                    truncation=True,
                    padding=True,
                )

                # Przenieś na odpowiednie urządzenie
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

                # Generuj embeddingi
                with torch.no_grad():
                    outputs = self.model(**inputs)
                    batch_embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()

                embeddings.extend(batch_embeddings.tolist())

        except Exception as e:
            logger.error(f"Error generating MMLW batch embeddings: {e}")
            embeddings = [[] for _ in texts]

        return embeddings

    def get_embedding_dimension(self) -> int:
        """Zwraca wymiar embeddingów (768 dla MMLW)"""
        return 768

    def is_available(self) -> bool:
        """Sprawdza czy model jest dostępny i zainicjalizowany"""
        return TRANSFORMERS_AVAILABLE and self.is_initialized

    async def health_check(self) -> Dict[str, Any]:
        """Sprawdza stan modelu"""
        return {
            "model_name": self.model_name,
            "is_available": self.is_available(),
            "transformers_available": TRANSFORMERS_AVAILABLE,
            "is_initialized": self.is_initialized,
            "device": str(self.device) if self.device else None,
            "embedding_dimension": self.get_embedding_dimension(),
            "initialization_in_progress": (
                self._initialization_task is not None
                and not self._initialization_task.done()
                if self._initialization_task
                else False
            ),
        }


# Globalna instancja klienta MMLW
mmlw_client = MMLWEmbeddingClient()
