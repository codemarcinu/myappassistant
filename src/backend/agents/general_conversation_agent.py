"""
General Conversation Agent

Agent obsługujący swobodne konwersacje na dowolny temat z wykorzystaniem:
- RAG (Retrieval-Augmented Generation) dla wiedzy z dokumentów
- Wyszukiwania internetowego (DuckDuckGo, Perplexity) dla aktualnych informacji
- Bielika jako głównego modelu językowego
"""

import asyncio
import logging
from typing import Any, Dict, Tuple, List, AsyncGenerator, Optional

import numpy as np

from ..core.cache_manager import cached_async, internet_cache, rag_cache
from ..core.decorators import handle_exceptions
from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.mmlw_embedding_client import mmlw_client
from ..core.perplexity_client import perplexity_client
from ..core.rag_document_processor import RAGDocumentProcessor
from ..core.rag_integration import RAGDatabaseIntegration
from ..core.vector_store import vector_store
from .base_agent import BaseAgent
from .interfaces import AgentResponse
from backend.integrations.web_search import web_search

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
        """Process user query with RAG and internet search in parallel"""
        try:
            query = input_data.get("query", "")
            session_id = input_data.get("session_id", "")
            use_perplexity = input_data.get("use_perplexity", False)
            use_bielik = input_data.get("use_bielik", True)

            logger.info(
                f"[GeneralConversationAgent] Processing query: {query[:100]}... use_perplexity={use_perplexity}, use_bielik={use_bielik}"
            )

            # Debug prints
            logger.debug("Input data: {}".format(input_data))
            logger.debug("Starting GeneralConversationAgent.process with parallel processing")

            # Uruchom równolegle pobieranie kontekstu z RAG i internetu
            rag_task = asyncio.create_task(self._get_rag_context(query))
            internet_task = asyncio.create_task(self._get_internet_context(query, use_perplexity))
            
            # Czekaj na zakończenie obu zadań
            rag_result, internet_context = await asyncio.gather(rag_task, internet_task)
            rag_context, rag_confidence = rag_result
            
            logger.info(f"RAG context confidence: {rag_confidence}")
            logger.info(f"Internet search completed: {bool(internet_context)}")

            # Wygeneruj odpowiedź z wykorzystaniem wszystkich źródeł
            logger.debug("Generating response with combined context")
            response = await self._generate_response(
                query, rag_context, internet_context, use_perplexity, use_bielik
            )

            logger.debug("GeneralConversationAgent.process completed successfully")
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

    @cached_async(rag_cache)
    async def _get_rag_context(self, query: str) -> Tuple[str, float]:
        """Pobiera kontekst z RAG i ocenia jego pewność."""
        try:
            # 1. Stwórz wektor dla zapytania
            query_embedding_list = await mmlw_client.embed_text(query)
            if not query_embedding_list:
                logger.warning("Failed to generate query embedding for RAG context.")
                return "", 0.0
            query_embedding = np.array([query_embedding_list], dtype=np.float32)

            # 2. Przeszukaj bazę wektorową (bez min_similarity)
            # Zwiększamy k, aby mieć więcej kandydatów do filtrowania
            search_results = await vector_store.search(query_embedding, k=5)

            if not search_results:
                return "", 0.0

            # 3. Ręcznie odfiltruj wyniki poniżej progu podobieństwa
            min_similarity_threshold = 0.7
            filtered_results = [
                (doc, sim)
                for doc, sim in search_results
                if sim >= min_similarity_threshold
            ]

            if not filtered_results:
                return "", 0.0

            # 4. Przetwórz i sformatuj odfiltrowane wyniki
            avg_confidence = sum(sim for _, sim in filtered_results) / len(
                filtered_results
            )

            # Pobierz dodatkowe dane z relacyjnej bazy danych
            db_context = await self.rag_integration.get_relevant_context(query)

            context_parts = []
            if filtered_results:
                doc_texts = [
                    f"- {doc.content} (Źródło: {doc.metadata.get('filename', 'Brak nazwy')})"
                    for doc, sim in filtered_results
                    if doc.content
                ]
                if doc_texts:
                    context_parts.append("Dokumenty:\n" + "\n".join(doc_texts[:2]))

            if db_context:
                context_parts.append("Dane z bazy:\n" + db_context)

            return "\n\n".join(context_parts) if context_parts else "", avg_confidence

        except Exception as e:
            logger.warning(f"Error getting RAG context: {str(e)}")
            return "", 0.0

    @cached_async(internet_cache)
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
            # Określ złożoność zapytania
            complexity = self._determine_query_complexity(query, rag_context, internet_context)
            logger.info(f"Determined query complexity: {complexity}")
            
            # Wybierz model na podstawie złożoności i flagi use_bielik
            model_name = self._select_model(complexity, use_bielik)
            logger.info(f"Selected model: {model_name}")

            response = await hybrid_llm_client.chat(
                messages=messages,
                model=model_name,
                force_complexity=complexity,
                stream=False,
            )

            if response and "message" in response and "content" in response["message"]:
                return response["message"]["content"]
            else:
                return "Przepraszam, nie udało się wygenerować odpowiedzi."

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "Przepraszam, wystąpił błąd podczas generowania odpowiedzi."
            
    def _determine_query_complexity(
        self, query: str, rag_context: str, internet_context: str
    ) -> ModelComplexity:
        """
        Określa złożoność zapytania na podstawie jego długości, zawartości i dostępnych kontekstów
        
        Returns:
            ModelComplexity.SIMPLE: Dla prostych zapytań (powitania, podziękowania)
            ModelComplexity.STANDARD: Dla typowych zapytań informacyjnych
            ModelComplexity.COMPLEX: Dla złożonych zapytań wymagających analizy lub twórczości
        """
        # Sprawdź czy to proste powitanie lub podziękowanie
        simple_phrases = [
            "cześć", "hej", "witaj", "dzień dobry", "dobry wieczór", "dobranoc",
            "dziękuję", "dzięki", "super", "świetnie", "ok", "dobrze",
            "rozumiem", "jasne", "tak", "nie", "może"
        ]
        
        query_lower = query.lower()
        
        # Jeśli to krótkie zapytanie i zawiera prostą frazę
        if len(query.split()) <= 3 and any(phrase in query_lower for phrase in simple_phrases):
            return ModelComplexity.SIMPLE
            
        # Jeśli mamy dużo kontekstu, to zapytanie jest złożone
        combined_context = (rag_context or "") + (internet_context or "")
        if len(combined_context) > 1000:
            return ModelComplexity.COMPLEX
            
        # Słowa kluczowe sugerujące złożone zapytanie
        complex_keywords = [
            "porównaj", "przeanalizuj", "wyjaśnij", "zinterpretuj", "oceń",
            "podsumuj", "zreferuj", "przedstaw argumenty", "uzasadnij",
            "zaprojektuj", "stwórz", "napisz", "wymyśl", "zaproponuj"
        ]
        
        if any(keyword in query_lower for keyword in complex_keywords):
            return ModelComplexity.COMPLEX
            
        # Domyślnie używamy standardowej złożoności
        return ModelComplexity.STANDARD
        
    def _select_model(self, complexity: ModelComplexity, use_bielik: bool) -> str:
        """
        Wybiera model na podstawie złożoności zapytania i preferencji użytkownika
        
        Args:
            complexity: Złożoność zapytania
            use_bielik: Czy używać modelu Bielik
            
        Returns:
            Nazwa modelu do użycia
        """
        if use_bielik:
            # Dla modelu Bielik
            if complexity == ModelComplexity.SIMPLE:
                return "SpeakLeash/bielik-7b-v2.3-instruct:Q5_K_M"  # Mniejszy model dla prostych zapytań
            else:
                return "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"  # Większy model dla złożonych
        else:
            # Dla modeli Gemma
            if complexity == ModelComplexity.SIMPLE:
                return "gemma3:2b"  # Mniejszy model dla prostych zapytań
            else:
                return "gemma3:12b"  # Większy model dla złożonych

    async def process_stream(self, input_data: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Process general conversation input with streaming response"""
        try:
            query = input_data.get("query", "")
            context = input_data.get("context", [])
            use_perplexity = input_data.get("use_perplexity", False)
            use_bielik = input_data.get("use_bielik", True)

            # Determine if this is a simple query
            is_simple_query = self._is_simple_query(query)
            
            # For simple queries, use a smaller model
            if is_simple_query:
                force_complexity = ModelComplexity.SIMPLE
                logger.info(f"Using SIMPLE model for query: {query}")
            else:
                force_complexity = None
                logger.info(f"Using standard model selection for query: {query}")

            # Run RAG and internet search in parallel
            rag_task = asyncio.create_task(self._get_rag_results(query))
            internet_task = asyncio.create_task(self._get_internet_results(query))
            
            # First yield a message that we're gathering information
            yield {
                "text": "Zbieram informacje...",
                "data": {"status": "gathering_info"},
                "success": True
            }
            
            # Wait for both tasks to complete
            rag_results, internet_results = await asyncio.gather(rag_task, internet_task)
            
            # Yield a message that we're processing the information
            yield {
                "text": "\nAnalizuję zebrane dane...",
                "data": {"status": "processing_info"},
                "success": True
            }
            
            # Combine context from both sources
            combined_context = self._combine_context(rag_results, internet_results)
            
            # Format the context for the LLM
            formatted_context = self._format_context_for_llm(combined_context)
            
            # Prepare messages for the LLM
            messages = self._prepare_messages(query, context, formatted_context)
            
            # Generate streaming response using the LLM
            stream_response = await hybrid_llm_client.chat(
                messages=messages,
                stream=True,
                use_perplexity=use_perplexity,
                use_bielik=use_bielik,
                force_complexity=force_complexity
            )
            
            # Clear the initial messages
            yield {
                "text": "",
                "data": {"status": "responding", "clear_previous": True},
                "success": True
            }

            # Stream the response chunks
            full_text = ""
            async for chunk in stream_response:
                if isinstance(chunk, dict) and "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    full_text += content
                    yield {
                        "text": content,
                        "data": {"status": "streaming"},
                        "success": True
                    }

            # Final chunk with complete data
            yield {
                "text": "",  # No additional text
                "data": {
                    "status": "complete",
                    "context_used": combined_context[:2]  # Include first 2 context items for transparency
                },
                "success": True
            }

        except Exception as e:
            logger.error(f"Error in GeneralConversationAgent streaming: {str(e)}")
            yield {
                "text": f"Przepraszam, wystąpił błąd: {str(e)}",
                "data": {"status": "error"},
                "success": False
            }

    def _is_simple_query(self, query: str) -> bool:
        """Determine if a query is simple based on length and complexity"""
        # Simple heuristic: short queries are likely simple
        if len(query) < 20:
            return True
            
        # Check for common simple phrases
        simple_phrases = [
            "dziękuję", "dzięki", "rozumiem", "ok", "dobrze", 
            "tak", "nie", "może", "cześć", "hej", "witaj",
            "do widzenia", "pa", "żegnaj"
        ]
        
        query_lower = query.lower()
        for phrase in simple_phrases:
            if phrase in query_lower:
                return True
                
        return False

    @cached_async(ttl=3600)  # Cache RAG results for 1 hour
    async def _get_rag_results(self, query: str) -> List[Dict[str, str]]:
        """Get results from RAG system with caching"""
        try:
            # Placeholder for actual RAG implementation
            # In a real system, this would query a vector database
            logger.info(f"Getting RAG results for: {query}")
            await asyncio.sleep(0.1)  # Simulate some processing time
            return []  # Return empty list as placeholder
        except Exception as e:
            logger.error(f"Error getting RAG results: {str(e)}")
            return []

    @cached_async(ttl=1800)  # Cache internet results for 30 minutes
    async def _get_internet_results(self, query: str) -> List[Dict[str, str]]:
        """Get results from internet search with caching"""
        try:
            logger.info(f"Getting internet results for: {query}")
            results = await web_search(query)
            return results[:3] if results else []  # Limit to top 3 results
        except Exception as e:
            logger.error(f"Error getting internet results: {str(e)}")
            return []

    def _combine_context(
        self, rag_results: List[Dict[str, str]], internet_results: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Combine context from RAG and internet search"""
        # Simple combination strategy: RAG results first, then internet
        combined = []
        
        # Add RAG results if available
        if rag_results:
            combined.extend(rag_results)
            
        # Add internet results if available
        if internet_results:
            combined.extend(internet_results)
            
        return combined

    def _format_context_for_llm(self, context: List[Dict[str, str]]) -> str:
        """Format context for LLM input"""
        if not context:
            return ""
            
        formatted = "Oto informacje, które mogą być pomocne:\n\n"
        
        for i, item in enumerate(context, 1):
            title = item.get("title", f"Źródło {i}")
            content = item.get("content", "")
            url = item.get("url", "")
            
            formatted += f"--- {title} ---\n"
            formatted += f"{content}\n"
            if url:
                formatted += f"Źródło: {url}\n"
            formatted += "\n"
            
        return formatted

    def _prepare_messages(
        self, query: str, conversation_history: List[Dict], context: str
    ) -> List[Dict[str, str]]:
        """Prepare messages for LLM with context and conversation history"""
        messages = []
        
        # System message with instructions
        system_message = (
            "Jesteś asystentem AI FoodSave, pomocnym i przyjaznym. "
            "Odpowiadaj zwięźle, ale kompletnie. "
            "Jeśli nie znasz odpowiedzi, przyznaj to zamiast wymyślać informacje."
        )
        
        if context:
            system_message += (
                "\n\nPoniżej znajdują się informacje kontekstowe, które mogą być pomocne "
                "w odpowiedzi na pytanie użytkownika. Wykorzystaj je, jeśli są przydatne:\n\n" + context
            )
            
        messages.append({"role": "system", "content": system_message})
        
        # Add conversation history
        for entry in conversation_history:
            if isinstance(entry, dict) and "role" in entry and "content" in entry:
                messages.append({"role": entry["role"], "content": entry["content"]})
                
        # Add current query
        messages.append({"role": "user", "content": query})
        
        return messages
