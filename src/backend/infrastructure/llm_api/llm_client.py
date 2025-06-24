import logging
from typing import Any, Dict, Optional

from backend.core.hybrid_llm_client import ModelComplexity, hybrid_llm_client

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using hybrid LLM client"""
        try:
            response = await hybrid_llm_client.generate_text(
                prompt=prompt, complexity=ModelComplexity.MEDIUM, **kwargs
            )
            return str(response.get("text", ""))
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return ""

    async def embed(self, text: str) -> list[float]:
        """Generate embeddings using hybrid LLM client"""
        try:
            embeddings = await hybrid_llm_client.generate_embeddings([text])
            return embeddings[0] if embeddings else []
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []

    async def chat(
        self, messages: list[Dict[str, str]], **kwargs: Any
    ) -> Optional[str]:
        """Chat using hybrid LLM client"""
        try:
            response = await hybrid_llm_client.chat(
                messages=messages, complexity=ModelComplexity.MEDIUM, **kwargs
            )
            return response.get("text", None)
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return None
