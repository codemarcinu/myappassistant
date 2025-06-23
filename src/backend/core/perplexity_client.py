"""
Perplexity API Client for enhanced search capabilities
"""

import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from backend.config import settings

logger = logging.getLogger(__name__)


class PerplexityClient:
    """Client for Perplexity AI API"""

    def __init__(self) -> None:
        self.api_key = settings.PERPLEXITY_API_KEY
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.http_client = httpx.AsyncClient(
            timeout=30.0, headers={"User-Agent": settings.USER_AGENT}
        )

        # Aktualne modele Perplexity (sprawdzone w dokumentacji 2024)
        self.available_models = [
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct",
            "mixtral-8x7b-instruct",
            "codellama-34b-instruct",
            "pplx-7b-online",
            "pplx-70b-online",
            "pplx-7b-chat",
            "pplx-70b-chat",
            "llama-3.1-8b-online",
            "llama-3.1-70b-online",
        ]

        # Domyślny model - używamy stabilnego modelu
        self.default_model = "llama-3.1-8b-instruct"

        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not found in environment variables")
            self.is_available = False
        else:
            self.is_available = True
            logger.info("Perplexity API client initialized")

    async def search(
        self,
        query: str,
        model: str | None = None,
        focus: Optional[str] = None,
        domain_filter: Optional[str] = None,
        max_results: int = 5,
    ) -> Dict[str, Any]:
        """
        Search using Perplexity API

        Args:
            query: Search query
            model: Model to use (if None, uses default)
            focus: Focus domain (e.g., "academic", "news", "writing")
            domain_filter: Specific domain filter
            max_results: Maximum number of results to return

        Returns:
            Dictionary with search results
        """
        if not self.is_available:
            return {
                "success": False,
                "error": "Perplexity API not available - no API key configured",
                "results": [],
            }

        # Użyj domyślnego modelu jeśli nie podano
        if model is None:
            model = self.default_model

        # Sprawdź czy model jest dostępny
        if model not in self.available_models:
            logger.warning(
                f"Model {model} not in available models, using default: {self.default_model}"
            )
            model = self.default_model

        try:
            # Prepare messages
            system_message = "You are a helpful search assistant. Provide accurate, up-to-date information with sources when possible."

            # Add domain focus if specified
            if focus:
                system_message += f" Focus on {focus} content."

            # Add domain filter if specified
            if domain_filter:
                system_message += f" Only search within {domain_filter}."

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": query},
            ]

            # Prepare request payload
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.1,
            }

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "User-Agent": settings.USER_AGENT,
            }

            logger.info(
                f"Sending Perplexity search request: {query[:100]}... with model: {model}"
            )

            response = await self.http_client.post(
                self.base_url, headers=headers, json=payload
            )

            response.raise_for_status()
            data = response.json()

            # Extract the response content
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0]["message"]["content"]

                # Parse response to extract structured information
                result = {
                    "success": True,
                    "query": query,
                    "content": content,
                    "model": model,
                    "usage": data.get("usage", {}),
                    "raw_response": data,
                }

                logger.info(f"Perplexity search successful for: {query[:50]}...")
                return result
            else:
                logger.error(f"Unexpected Perplexity response format: {data}")
                return {
                    "success": False,
                    "error": "Unexpected response format from Perplexity API",
                    "results": [],
                }

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Perplexity API HTTP error: {e.response.status_code} - {e.response.text}"
            )

            # Szczegółowa obsługa błędów HTTP
            if e.response.status_code == 400:
                error_msg = "Invalid request to Perplexity API - check model name and parameters"
            elif e.response.status_code == 401:
                error_msg = "Unauthorized - check Perplexity API key"
            elif e.response.status_code == 429:
                error_msg = "Rate limit exceeded - try again later"
            elif e.response.status_code == 500:
                error_msg = "Perplexity API internal error - try again later"
            else:
                error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"

            return {"success": False, "error": error_msg, "results": []}
        except Exception as e:
            logger.error(f"Perplexity API error: {str(e)}")
            return {"success": False, "error": f"API error: {str(e)}", "results": []}

    async def search_with_sources(
        self, query: str, model: str | None = None
    ) -> Dict[str, Any]:
        """
        Search with explicit request for sources

        Args:
            query: Search query
            model: Model to use

        Returns:
            Dictionary with search results and sources
        """
        enhanced_query = (
            f"{query}\n\nPlease provide sources and citations for your response."
        )
        return await self.search(enhanced_query, model)

    async def academic_search(self, query: str) -> Dict[str, Any]:
        """
        Academic-focused search

        Args:
            query: Search query

        Returns:
            Dictionary with academic search results
        """
        return await self.search(
            query, model="llama-3.1-70b-instruct", focus="academic"
        )

    async def news_search(self, query: str) -> Dict[str, Any]:
        """
        News-focused search

        Args:
            query: Search query

        Returns:
            Dictionary with news search results
        """
        return await self.search(query, model="llama-3.1-8b-instruct", focus="news")

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models

        Returns:
            List of available model names
        """
        return self.available_models.copy()

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Perplexity API

        Returns:
            Dictionary with test results
        """
        if not self.is_available:
            return {"success": False, "error": "API not configured - no API key"}

        try:
            # Simple test query
            result = await self.search("test", max_results=1)
            return {
                "success": result["success"],
                "error": result.get("error"),
                "model_used": result.get("model"),
            }
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}

    async def close(self) -> None:
        """Close HTTP client"""
        await self.http_client.aclose()

    def is_configured(self) -> bool:
        """Check if Perplexity API is properly configured"""
        return self.is_available and self.api_key is not None

    async def stream_search(
        self,
        query: str,
        model: str | None = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform a streaming search with Perplexity
        """
        if not self.is_available:
            yield {
                "success": False,
                "error": "Perplexity API not available - no API key configured",
            }
            return

        model = model or self.default_model
        if model not in self.available_models:
            logger.warning(
                f"Model {model} not available, using default {self.default_model}"
            )
            model = self.default_model

        try:
            messages = [
                {"role": "system", "content": "You are a helpful search assistant."},
                {"role": "user", "content": query},
            ]
            payload = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            }

            async with self.http_client.stream(
                "POST", self.base_url, headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    if chunk:
                        yield {"success": True, "chunk": chunk.decode("utf-8")}
        except httpx.HTTPStatusError as e:
            logger.error(f"Perplexity API stream error: {e.response.text}")
            yield {"success": False, "error": f"HTTP error: {e.response.text}"}
        except Exception as e:
            logger.error(f"Perplexity stream error: {str(e)}")
            yield {"success": False, "error": str(e)}


# Global instance
perplexity_client = PerplexityClient()
