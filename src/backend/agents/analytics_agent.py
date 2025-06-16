from typing import Any, Dict

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.core.crud import get_summary


class AnalyticsAgent(BaseAgent):
    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        db = context["db"]
        query_params = context["query_params"]

        summary = await get_summary(db, query_params)

        return AgentResponse(
            text="Analytics generated.",
            data={"summary": summary},
            success=True,
        )
