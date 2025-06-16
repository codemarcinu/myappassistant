from typing import Any, Dict

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.agents.prompts import get_meal_plan_prompt
from backend.core.crud import get_available_products
from backend.core.llm_client import llm_client


class MealPlannerAgent(BaseAgent):
    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        db = context["db"]
        available_products = await get_available_products(db)

        products_dict = [
            {"name": p.name, "quantity": p.quantity} for p in available_products
        ]

        prompt = get_meal_plan_prompt(products_dict)

        response = await llm_client.chat(
            model="gemma3:12b",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful meal planning assistant.",
                },
                {"role": "user", "content": prompt},
            ],
            stream=False,
        )

        if response and "message" in response:
            content = response["message"]["content"]
            # TODO: Parse the response and extract the meal plan and shopping list
            return AgentResponse(
                text=content,
                data={"meal_plan": [], "shopping_list": []},
                success=True,
            )
        else:
            return AgentResponse(
                text="Failed to generate meal plan.",
                data={},
                success=False,
            )
