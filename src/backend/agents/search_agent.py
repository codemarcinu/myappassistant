import logging
from typing import Any, Dict

import httpx

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.config import settings
from backend.core.decorators import handle_exceptions
from backend.core.hybrid_llm_client import hybrid_llm_client
from backend.core.perplexity_client import perplexity_client

logger = logging.getLogger(__name__)


class SearchAgentInput:
    """Input model for SearchAgent"""

    def __init__(self, query: str, model: str = None, max_results: int = 5):
        self.query = query
        self.model = model or "gemma3:12b"  # Użyj domyślnego modelu
        self.max_results = max_results


class SearchAgent(BaseAgent):
    """Agent that performs web searches using DuckDuckGo and Perplexity"""

    def __init__(self, name: str = "SearchAgent", **kwargs):
        super().__init__(name, **kwargs)
        self.search_url = "https://api.duckduckgo.com/"
        self.http_client = httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": settings.USER_AGENT}
        )
        self.llm_client = hybrid_llm_client  # Dodaję atrybut llm_client dla testów
        self.web_search = perplexity_client  # Dodaję atrybut web_search dla testów

    @handle_exceptions(max_retries=2)
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Main processing method - performs search and returns results in a stream"""
        query = input_data.get("query", "")
        if not query:
            return AgentResponse(
                success=False,
                error="Query is required",
                text="Przepraszam, ale potrzebuję zapytania do wyszukania.",
            )

        max_results = input_data.get("max_results", 5)
        use_perplexity = input_data.get("use_perplexity", True)  # Domyślnie Perplexity

        async def stream_generator():
            try:
                yield "Rozpoczynam wyszukiwanie...\n"

                if use_perplexity:
                    logger.info(f"Using Perplexity for search query: {query}")
                    yield "Korzystam z Perplexity...\n"
                    # Perplexity API nie wspiera streamingu w obecnym kliencie,
                    # więc wykonujemy pełne zapytanie i zwracamy wynik jako pojedynczy chunk.
                    search_result = await perplexity_client.search(
                        query, model=None, max_results=max_results
                    )
                    if search_result["success"]:
                        yield search_result["content"]
                    else:
                        yield f"Błąd podczas wyszukiwania w Perplexity: {search_result['error']}"
                else:
                    # Alternatywna logika (np. DuckDuckGo), która może wspierać streaming
                    logger.info(f"Using DuckDuckGo for search query: {query}")
                    yield "Korzystam z DuckDuckGo...\n"
                    duckduckgo_result = await self._duckduckgo_search(query)
                    if duckduckgo_result["success"]:
                        yield duckduckgo_result["content"]
                    else:
                        yield f"Błąd podczas wyszukiwania w DuckDuckGo: {duckduckgo_result['error']}"

            except Exception as e:
                logger.error(f"[SearchAgent] Error during stream generation: {e}")
                yield f"Wystąpił wewnętrzny błąd: {e}"

        return AgentResponse(
            success=True,
            text_stream=stream_generator(),
            message="Search stream started.",
        )

    async def _perform_search(
        self, query: str, model: str, max_results: int
    ) -> Dict[str, Any]:
        """Perform search using Perplexity API"""
        try:
            # Translate query to English for better results
            english_query = await self._translate_to_english(query, model)

            # Perform search with Perplexity
            result = await perplexity_client.search(
                query=english_query,
                model=None,  # Użyj domyślnego modelu
                max_results=max_results,
            )

            if result["success"]:
                # Translate response back to Polish if needed
                polish_response = await self._translate_to_polish(
                    result["content"], model
                )
                result["content"] = polish_response

            return result

        except Exception as e:
            logger.error(f"Error in Perplexity search: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def _duckduckgo_search(self, query: str) -> Dict[str, Any]:
        """Fallback search using DuckDuckGo"""
        try:
            # Simple DuckDuckGo search implementation
            search_url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1&skip_disambig=1"

            response = await self.http_client.get(search_url)
            response.raise_for_status()

            data = response.json()

            # Extract relevant information
            abstract = data.get("Abstract", "")
            answer = data.get("Answer", "")
            related_topics = data.get("RelatedTopics", [])

            # Combine results
            content_parts = []
            if answer:
                content_parts.append(f"Odpowiedź: {answer}")
            if abstract:
                content_parts.append(f"Opis: {abstract}")
            if related_topics:
                topics = [topic.get("Text", "") for topic in related_topics[:3]]
                content_parts.append(f"Powiązane tematy: {'; '.join(topics)}")

            content = (
                "\n\n".join(content_parts)
                if content_parts
                else "Nie znaleziono odpowiednich wyników."
            )

            return {
                "success": True,
                "content": content,
                "source": "duckduckgo",
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error in DuckDuckGo search: {e}")
            return {"success": False, "error": str(e), "content": ""}

    async def _translate_to_english(self, polish_query: str, model: str) -> str:
        """Translate Polish query to English for better search results"""
        prompt = (
            f"Przetłumacz poniższe zapytanie z języka polskiego na angielski:\n\n"
            f"Zapytanie: '{polish_query}'\n\n"
            f"Zwróć tylko tłumaczenie, bez dodatkowego tekstu."
        )

        try:
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który tłumaczy zapytania z polskiego na angielski.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not isinstance(response, dict):
                return polish_query

            # Sprawdź różne możliwe struktury odpowiedzi
            content = None
            if "message" in response:
                message = response["message"]
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                elif isinstance(message, list) and len(message) > 0:
                    # Jeśli message jest listą, weź pierwszy element
                    first_msg = message[0]
                    if isinstance(first_msg, dict) and "content" in first_msg:
                        content = first_msg["content"]

            if not content:
                return polish_query

            english_query = content.strip()
            logger.info(
                f"[SearchAgent] Translated '{polish_query}' to '{english_query}'"
            )
            return english_query
        except Exception as e:
            logger.error(f"Error translating query: {e}")
            return polish_query

    async def _translate_to_polish(self, english_content: str, model: str) -> str:
        """Translate English content back to Polish"""
        prompt = (
            f"Przetłumacz poniższą treść z języka angielskiego na polski:\n\n"
            f"Treść: '{english_content}'\n\n"
            f"Zwróć tylko tłumaczenie, bez dodatkowego tekstu."
        )

        try:
            response = await hybrid_llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który tłumaczy treści z angielskiego na polski.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not isinstance(response, dict):
                return english_content

            # Sprawdź różne możliwe struktury odpowiedzi
            content = None
            if "message" in response:
                message = response["message"]
                if isinstance(message, dict) and "content" in message:
                    content = message["content"]
                elif isinstance(message, list) and len(message) > 0:
                    # Jeśli message jest listą, weź pierwszy element
                    first_msg = message[0]
                    if isinstance(first_msg, dict) and "content" in first_msg:
                        content = first_msg["content"]

            if not content:
                return english_content

            polish_content = content.strip()
            logger.info("[SearchAgent] Translated response to Polish")
            return polish_content
        except Exception as e:
            logger.error(f"Error translating response: {e}")
            return english_content

    @handle_exceptions(max_retries=1)
    def get_dependencies(self) -> list[str]:
        """Return list of dependencies this agent requires"""
        return ["httpx", "hybrid_llm_client", "perplexity_client"]

    def get_metadata(self) -> dict:
        """Return metadata about this agent"""
        return {
            "name": self.name,
            "description": "Agent that performs web searches using Perplexity and DuckDuckGo",
            "version": "1.0.0",
            "search_url": self.search_url,
            "capabilities": ["web_search", "translation", "fallback_search"],
        }

    def is_healthy(self) -> bool:
        """Check if the agent is healthy and ready to process requests"""
        return True  # Simple health check - could be enhanced
