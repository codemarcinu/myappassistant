from typing import Any, Dict

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.agents.prompts import get_categorization_prompt
from backend.core.llm_client import llm_client


class CategorizationAgent(BaseAgent):
    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        product_name = context["product_name"]

        prompt = get_categorization_prompt(product_name)

        response = await llm_client.chat(
            model="gemma3:12b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful categorization assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        if response and "message" in response:
            content = response["message"]["content"]
            # TODO: Parse the response and extract the category
            return AgentResponse(
                text=content,
                data={"category": ""},
                success=True,
            )
        else:
            return AgentResponse(
                text="Failed to categorize product.",
                data={},
                success=False,
            )
