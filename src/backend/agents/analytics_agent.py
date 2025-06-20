from typing import Any, Dict

from ..core.crud import get_summary
from .base_agent import BaseAgent
from .interfaces import AgentResponse


class AnalyticsAgent(BaseAgent):
    def __init__(
        self,
        name: str = "AnalyticsAgent",
        error_handler=None,
        fallback_manager=None,
        **kwargs
    ):
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        db = context["db"]
        query_params = context["query_params"]

        summary = await get_summary(db, query_params)

        return AgentResponse(
            text="Analytics generated.",
            data={"summary": summary},
            success=True,
        )
