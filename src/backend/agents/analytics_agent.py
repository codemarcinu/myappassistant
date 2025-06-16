from typing import Any, Dict

from ..core.crud import get_summary
from .base_agent import AgentResponse, BaseAgent


class AnalyticsAgent(BaseAgent):
    def __init__(self, name: str):
        super().__init__(name)

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        db = context["db"]
        query_params = context["query_params"]

        summary = await get_summary(db, query_params)

        return AgentResponse(
            text="Analytics generated.",
            data={"summary": summary},
            success=True,
        )
