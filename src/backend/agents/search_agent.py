import logging
from typing import Any, AsyncGenerator, Dict, List

import httpx

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    """Agent that performs web searches using DuckDuckGo"""

    def __init__(self, name: str = "SearchAgent"):
        super().__init__(name)
        self.search_url = "https://api.duckduckgo.com/"

    async def process(self, input_data: Any) -> AgentResponse:
        """Process a search request and return formatted results"""
        if isinstance(input_data, dict):
            try:
                query = input_data.get("query", "")
                model = input_data.get("model", "gemma3:12b")  # Default model
                if not query:
                    return AgentResponse(
                        success=False,
                        error="Brak zapytania wyszukiwania.",
                        text="Proszę podać zapytanie wyszukiwania.",
                    )

                # Get search results
                search_results = await self._perform_search(query)
                if not search_results:

                    async def empty_stream():
                        if False:
                            yield

                    return AgentResponse(
                        success=True,
                        text=f"Brak wyników dla zapytania: {query}",
                        text_stream=empty_stream(),
                    )

                # Format search results using LLM
                response_stream = self._format_search_results(
                    query, search_results, model
                )

                return AgentResponse(
                    success=True,
                    data={"query": query, "results": search_results},
                    text_stream=response_stream,
                    message=f"Wyniki wyszukiwania dla: {query}",
                )
            except Exception as e:
                logger.error(f"Error processing search request: {e}")
                return AgentResponse(
                    success=False,
                    error=f"Wystąpił błąd podczas przetwarzania zapytania: {str(e)}",
                    text="Przepraszam, wystąpił problem z wykonaniem wyszukiwania.",
                )

        return AgentResponse(
            success=False,
            error="Nieprawidłowy format danych wejściowych.",
            text="Przepraszam, nie mogłem przetworzyć tego zapytania.",
        )

    async def _perform_search(self, query: str) -> List[Dict[str, str]]:
        """Perform a search using DuckDuckGo API"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.search_url,
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "no_redirect": 1,
                    },
                    timeout=10.0,
                )
                response.raise_for_status()
                data = response.json()
                logger.debug(f"Search API response for '{query}': {data}")

                # Extract relevant fields from the response
                results = []
                if "Results" in data:
                    for r in data["Results"]:
                        if r.get("Text") and r.get("FirstURL"):
                            results.append(
                                {
                                    "title": r.get("Text"),
                                    "url": r.get("FirstURL"),
                                    "snippet": r.get("Result", ""),
                                }
                            )
                if "RelatedTopics" in data:
                    for r in data["RelatedTopics"]:
                        if r.get("Text") and r.get("FirstURL"):
                            results.append(
                                {
                                    "title": r.get("Text"),
                                    "url": r.get("FirstURL"),
                                    "snippet": r.get("Result", ""),
                                }
                            )

                if not results:
                    # Fallback to simple result if no structured data found
                    if "AbstractText" in data and data["AbstractText"]:
                        results.append(
                            {
                                "title": data.get("Heading", "Wynik wyszukiwania"),
                                "url": data.get("AbstractURL", ""),
                                "snippet": data["AbstractText"],
                            }
                        )

                return results
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error performing search for '{query}': {e}")
            return []
        except httpx.RequestError as e:
            logger.error(f"Network error performing search for '{query}': {e}")
            return []
        except Exception as e:
            logger.error(f"Error performing search for '{query}': {e}", exc_info=True)
            return []

    async def _extract_search_query(self, user_input: str, model: str) -> str:
        """Extract search query from user input using LLM"""
        prompt = (
            f"Przeanalizuj poniższą wiadomość użytkownika i wyodrębnij zapytanie wyszukiwania:\n\n"
            f"Wiadomość: '{user_input}'\n\n"
            f"Zwróć tylko zapytanie wyszukiwania, bez dodatkowego tekstu."
        )

        try:
            response = await llm_client.chat(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który ekstrahuje zapytania wyszukiwania z tekstu.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not response.get("message"):
                return user_input

            query = response["message"]["content"].strip()
            return query
        except Exception as e:
            logger.error(f"Error extracting search query: {e}")
            return user_input

    async def _format_search_results(
        self, query: str, results: List[Dict[str, str]], model: str
    ) -> AsyncGenerator[str, None]:
        """Format search results into a user-friendly response using LLM"""
        try:
            # Create a summary of search results for the LLM
            results_summary = f"Wyniki wyszukiwania dla zapytania: '{query}'\n\n"

            for i, result in enumerate(results, 1):
                title = result.get("title", "Brak tytułu")
                url = result.get("url", "")
                snippet = result.get("snippet", "Brak opisu")

                results_summary += f"{i}. {title}\n"
                results_summary += f"   URL: {url}\n"
                results_summary += f"   Opis: {snippet}\n\n"

            # Let the LLM format this into a nice response
            prompt = (
                f"Na podstawie poniższych wyników wyszukiwania, utwórz przyjazną i "
                f"pomocną odpowiedź w języku polskim. Uwzględnij najważniejsze "
                f"informacje z wyników i podaj źródła (URL):\n\n{results_summary}"
            )

            async for chunk in llm_client.generate_stream(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem wyszukiwania.",
                    },
                    {"role": "user", "content": prompt},
                ],
            ):
                yield chunk["message"]["content"]

        except Exception as e:
            logger.error(f"Error formatting search results: {e}")

            # Simple fallback format if LLM fails
            formatted_result = f"Wyniki wyszukiwania dla: {query}\n\n"
            for i, result in enumerate(results, 1):
                formatted_result += f"{i}. {result.get('title', 'Brak tytułu')}\n"
                formatted_result += f"   {result.get('url', '')}\n"
                formatted_result += f"   {result.get('snippet', 'Brak opisu')}\n\n"

            yield formatted_result
