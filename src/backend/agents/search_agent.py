import logging
from typing import Any, Dict, List

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
                if not query:
                    return AgentResponse(
                        success=False,
                        error="Brak zapytania wyszukiwania.",
                        text="Proszę podać zapytanie wyszukiwania.",
                    )

                # Get search results
                search_results = await self._perform_search(query)
                if not search_results:
                    return AgentResponse(
                        success=False,
                        error=f"Nie znaleziono wyników dla zapytania: {query}",
                        text=f"Nie znaleziono wyników dla zapytania: {query}",
                    )

                # Format search results using LLM
                formatted_response = await self._format_search_results(
                    query, search_results
                )

                return AgentResponse(
                    success=True,
                    data={"query": query, "results": search_results},
                    text=formatted_response,
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
            # In a real implementation, we would call the DuckDuckGo API
            # For demo purposes, we'll simulate the API response

            # This is a mock implementation - in a real scenario we would use:
            # async with httpx.AsyncClient() as client:
            #     response = await client.get(
            #         self.search_url,
            #         params={"q": query, "format": "json", "no_html": 1, "no_redirect": 1}
            #     )
            #     data = response.json()

            # For demo purposes, return mock results
            mock_results = [
                {
                    "title": f"Result 1 for {query}",
                    "url": f"https://example.com/result1?q={query}",
                    "snippet": f"This is a sample search result for {query}. It contains information related to your search query.",
                },
                {
                    "title": f"Result 2 for {query}",
                    "url": f"https://example.com/result2?q={query}",
                    "snippet": f"Another search result related to {query}. This result provides additional context and information.",
                },
                {
                    "title": f"Result 3 for {query}",
                    "url": f"https://example.com/result3?q={query}",
                    "snippet": f"A third search result for {query} with more details and information from various sources.",
                },
            ]

            return mock_results
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []

    async def _extract_search_query(self, user_input: str) -> str:
        """Extract search query from user input using LLM"""
        prompt = (
            f"Przeanalizuj poniższą wiadomość użytkownika i wyodrębnij zapytanie wyszukiwania:\n\n"
            f"Wiadomość: '{user_input}'\n\n"
            f"Zwróć tylko zapytanie wyszukiwania, bez dodatkowego tekstu."
        )

        try:
            response = await llm_client.chat(
                model="gemma3:12b",
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
        self, query: str, results: List[Dict[str, str]]
    ) -> str:
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

            response = await llm_client.chat(
                model="gemma3:12b",
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem wyszukiwania.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            if not response or not response.get("message"):
                return results_summary

            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Error formatting search results: {e}")

            # Simple fallback format if LLM fails
            formatted_result = f"Wyniki wyszukiwania dla: {query}\n\n"
            for i, result in enumerate(results, 1):
                formatted_result += f"{i}. {result.get('title', 'Brak tytułu')}\n"
                formatted_result += f"   {result.get('url', '')}\n"
                formatted_result += f"   {result.get('snippet', 'Brak opisu')}\n\n"

            return formatted_result
