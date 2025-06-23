import logging
from typing import Any, Dict, List, Optional

from backend.core.interfaces import AgentResponse
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class FallbackStrategy:
    """Base class for fallback strategies."""

    async def execute(
        self, input_data: Dict[str, Any], error: Exception
    ) -> Optional[AgentResponse]:
        raise NotImplementedError


class PromptRewritingStrategy(FallbackStrategy):
    """Rewrites the prompt to be simpler."""

    async def execute(
        self, input_data: Dict[str, Any], error: Exception
    ) -> Optional[AgentResponse]:
        try:
            original_query = input_data.get("query", "")
            prompt = f"Rewrite the following query to be simpler: {original_query}"
            response = await llm_client.chat(
                messages=[{"role": "user", "content": prompt}]
            )
            rewritten_query = response["message"]["content"]
            return AgentResponse(
                success=True,
                data={"query": rewritten_query},
                metadata={
                    "original_query": original_query,
                    "rewritten_query": rewritten_query,
                },
            )
        except Exception as e:
            logger.warning(f"Prompt rewriting failed: {e}")
            return None


class SimplifiedModelStrategy(FallbackStrategy):
    """Uses a simpler/cheaper model for the query."""

    async def execute(
        self, input_data: Dict[str, Any], error: Exception
    ) -> Optional[AgentResponse]:
        try:
            input_data["model"] = "gemma:2b"  # or other simpler model
            response = await llm_client.chat(
                messages=[{"role": "user", "content": input_data.get("query", "")}]
            )
            return AgentResponse(success=True, text=response["message"]["content"])
        except Exception as e:
            logger.warning(f"Simplified model strategy failed: {e}")
            return None


class MinimalResponseStrategy(FallbackStrategy):
    """Provides a minimal, static response."""

    async def execute(
        self, input_data: Dict[str, Any], error: Exception
    ) -> Optional[AgentResponse]:
        return AgentResponse(
            success=False, error="Przepraszam, nie udało się przetworzyć zapytania."
        )


class FallbackManager:
    """Manages fallback strategies for agent failures."""

    def __init__(self) -> None:
        self.strategies: List[FallbackStrategy] = [
            PromptRewritingStrategy(),
            SimplifiedModelStrategy(),
            MinimalResponseStrategy(),  # Ultimate fallback
        ]

    async def execute_fallback(
        self, input_data: Dict[str, Any], error: Exception
    ) -> AgentResponse:
        """Executes fallback strategies in order until one succeeds."""
        for strategy in self.strategies:
            response = await strategy.execute(input_data, error)
            if response and response.success:
                return response
        # This should not be reached if MinimalResponseStrategy is always last
        return AgentResponse(success=False, error="Wszystkie opcje awaryjne zawiodły.")
