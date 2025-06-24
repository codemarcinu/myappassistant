from typing import Any, Dict

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.agents.prompts import get_categorization_prompt
from backend.core.hybrid_llm_client import hybrid_llm_client


class CategorizationAgent(BaseAgent):
    def __init__(
        self,
        name: str = "CategorizationAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        product_name = context["product_name"]

        # Sprawdź flagę use_bielik
        use_bielik = context.get("use_bielik", True)
        model = (
            "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
            if use_bielik
            else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        )

        prompt = get_categorization_prompt(product_name)

        response = await hybrid_llm_client.chat(
            model=model,
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
