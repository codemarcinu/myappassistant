"""
General Conversation Agent

Agent obsługujący swobodne konwersacje na dowolny temat z wykorzystaniem:
- RAG (Retrieval-Augmented Generation) dla wiedzy z dokumentów
- Wyszukiwania internetowego (DuckDuckGo, Perplexity) dla aktualnych informacji
- Bielika jako głównego modelu językowego
"""

import logging
from typing import Any, Dict

from ..core.decorators import handle_exceptions
from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.perplexity_client import perplexity_client
from ..core.rag_document_processor import RAGDocumentProcessor
from ..core.rag_integration import RAGDatabaseIntegration
from ..core.vector_store import vector_store
from .base_agent import BaseAgent
from .interfaces import AgentResponse

logger = logging.getLogger(__name__)


class GeneralConversationAgent(BaseAgent):
    """Agent do obsługi swobodnych konwersacji z wykorzystaniem RAG i wyszukiwania internetowego"""

    def __init__(self, name: str = "GeneralConversationAgent"):
        super().__init__(name)
        self.rag_processor = RAGDocumentProcessor()
        self.rag_integration = RAGDatabaseIntegration(self.rag_processor)
        self.description = "Agent do obsługi swobodnych konwersacji z wykorzystaniem RAG i wyszukiwania internetowego"

    @handle_exceptions(max_retries=2)
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Przetwarza zapytanie użytkownika w kontekście swobodnej konwersacji"""
        try:
            # Wyciągnij dane wejściowe
            query = input_data.get("query", "")
            use_perplexity = input_data.get("use_perplexity", False)
            use_bielik = input_data.get("use_bielik", True)  # Domyślnie Bielik
            session_id = input_data.get("session_id", "")

            if not query:
                return AgentResponse(
                    success=False,
                    error="Query is required",
                    text="Przepraszam, ale potrzebuję zapytania do przetworzenia.",
                )

            logger.info(
                f"[GeneralConversationAgent] Processing query: {query[:100]}... use_perplexity={use_perplexity}, use_bielik={use_bielik}"
            )

            # 1. Zawsze próbuj pobrać kontekst z RAG
            rag_context, rag_confidence = await self._get_rag_context(query)
            logger.info(f"RAG context confidence: {rag_confidence}")

            # 2. Decyzja o przeszukaniu internetu
            internet_context = ""
            # Jeśli pewność RAG jest niska, szukaj w internecie
            if rag_confidence < 0.75:  # Próg pewności
                logger.info(
                    f"RAG confidence is low ({rag_confidence}), searching internet."
                )
                internet_context = await self._get_internet_context(
                    query, use_perplexity
                )

            # 3. Wygeneruj odpowiedź z wykorzystaniem wszystkich źródeł
            response = await self._generate_response(
                query, rag_context, internet_context, use_perplexity, use_bielik
            )

            return AgentResponse(
                success=True,
                text=response,
                data={
                    "query": query,
                    "used_rag": bool(rag_context),
                    "used_internet": bool(internet_context),
                    "rag_confidence": rag_confidence,
                    "use_perplexity": use_perplexity,
                    "use_bielik": use_bielik,
                    "session_id": session_id,
                },
            )

        except Exception as e:
            logger.error(f"Error in GeneralConversationAgent: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Błąd przetwarzania: {str(e)}",
                text="Przepraszam, wystąpił błąd podczas przetwarzania Twojego zapytania.",
            )

    async def _get_rag_context(self, query: str) -> (str, float):
        """Pobiera kontekst z RAG i ocenia jego pewność."""
        try:
            # Pobierz dokumenty z RAG
            documents = await vector_store.search(query, k=3, min_similarity=0.7)

            if not documents:
                return "", 0.0

            # Oblicz średnią pewność
            avg_confidence = sum(doc.get("similarity", 0) for doc in documents) / len(
                documents
            )

            # Pobierz dane z bazy danych (zakupy, przepisy, etc.)
            db_context = await self.rag_integration.get_relevant_context(query)

            context_parts = []

            if documents:
                doc_texts = [
                    f"- {doc.get('content', '')} (Źródło: {doc.get('metadata', {}).get('filename', 'Brak nazwy')})"
                    for doc in documents
                    if doc.get("content")
                ]
                if doc_texts:
                    context_parts.append("Dokumenty:\n" + "\n".join(doc_texts[:2]))

            if db_context:
                context_parts.append("Dane z bazy:\n" + db_context)

            return "\n\n".join(context_parts) if context_parts else "", avg_confidence

        except Exception as e:
            logger.warning(f"Error getting RAG context: {str(e)}")
            return "", 0.0

    async def _get_internet_context(self, query: str, use_perplexity: bool) -> str:
        """Pobiera informacje z internetu"""
        try:
            if use_perplexity:
                # Użyj Perplexity dla lepszych wyników
                search_result = await perplexity_client.search(query, max_results=3)
                if search_result.get("success") and search_result.get("results"):
                    return "Informacje z internetu:\n" + "\n".join(
                        [
                            result.get("content", "")
                            for result in search_result["results"][:2]
                        ]
                    )
            else:
                # Użyj lokalnego wyszukiwania
                from .search_agent import SearchAgent

                search_agent = SearchAgent()
                search_result = await search_agent.process(
                    {"query": query, "max_results": 3, "use_perplexity": False}
                )

                if search_result.success and search_result.data:
                    results = search_result.data.get("results", [])
                    if results:
                        return "Informacje z internetu:\n" + "\n".join(
                            [result.get("content", "") for result in results[:2]]
                        )

            return ""

        except Exception as e:
            logger.warning(f"Error getting internet context: {str(e)}")
            return ""

    async def _generate_response(
        self,
        query: str,
        rag_context: str,
        internet_context: str,
        use_perplexity: bool,
        use_bielik: bool,
    ) -> str:
        """Generuje odpowiedź z wykorzystaniem wszystkich źródeł informacji"""

        # Buduj system prompt
        system_prompt = """Jesteś pomocnym asystentem AI prowadzącym swobodne konwersacje.
        Twoim zadaniem jest udzielanie dokładnych, pomocnych i aktualnych odpowiedzi na pytania użytkownika.

        Wykorzystuj dostępne źródła informacji:
        1. Wiedzę ogólną
        2. Informacje z dokumentów (jeśli dostępne)
        3. Dane z bazy (jeśli dostępne)
        4. Informacje z internetu (jeśli dostępne)

        Zawsze podawaj źródła informacji gdy to możliwe i odróżniaj fakty od opinii.
        Odpowiadaj w języku polskim, chyba że użytkownik prosi o inną wersję językową."""

        # Buduj kontekst
        context_parts = []
        if rag_context:
            context_parts.append(f"KONTEKST Z DOKUMENTÓW I BAZY DANYCH:\n{rag_context}")
        if internet_context:
            context_parts.append(f"INFORMACJE Z INTERNETU:\n{internet_context}")

        context_text = "\n\n".join(context_parts) if context_parts else ""

        # Buduj wiadomości
        messages = [{"role": "system", "content": system_prompt}]

        if context_text:
            messages.append(
                {
                    "role": "system",
                    "content": f"DOSTĘPNE INFORMACJE:\n{context_text}\n\nUżyj tych informacji do udzielenia dokładnej odpowiedzi.",
                }
            )

        messages.append({"role": "user", "content": query})

        # Generuj odpowiedź używając odpowiedniego modelu
        try:
            # Wybierz model na podstawie flagi use_bielik
            model_name = (
                "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                if use_bielik
                else "gemma3:12b"
            )

            response = await hybrid_llm_client.chat(
                messages=messages,
                model=model_name,
                force_complexity=ModelComplexity.STANDARD,
                stream=False,
            )

            if response and "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                return "Przepraszam, nie udało się wygenerować odpowiedzi."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Przepraszam, wystąpił błąd podczas generowania odpowiedzi."
