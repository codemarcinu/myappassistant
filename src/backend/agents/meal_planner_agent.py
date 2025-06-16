import logging
from typing import Any, Dict

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.agents.prompts import get_meal_plan_prompt
from backend.agents.utils import extract_json_from_text
from backend.core.crud import get_available_products
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class MealPlannerAgent(BaseAgent):
    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        try:
            db = context["db"]
            available_products = await get_available_products(db)

            products_dict = [
                {"name": p.name, "quantity": p.quantity} for p in available_products
            ]

            prompt = get_meal_plan_prompt(products_dict)

            async def response_generator():
                full_response = ""
                try:
                    async for chunk in llm_client.generate_stream(
                        model="gemma3:12b",
                        messages=[
                            {
                                "role": "system",
                                "content": "You are a helpful meal planning assistant.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                    ):
                        content = chunk["message"]["content"]
                        full_response += content
                        yield content

                    # After streaming, parse the full_response to extract structured data
                    parsed_data = extract_json_from_text(full_response)
                    logger.debug(f"Meal plan data extracted: {parsed_data}")
                except Exception as e:
                    logger.error(f"Error in meal plan streaming: {e}", exc_info=True)
                    yield "Wystąpił błąd podczas generowania planu posiłków."

            return AgentResponse(
                success=True,
                text_stream=response_generator(),
                message="Meal plan stream started.",
            )
        except Exception as e:
            logger.error(f"Error in meal planner process: {e}", exc_info=True)
            return AgentResponse(
                success=False,
                error=str(e),
                text="Wystąpił błąd podczas planowania posiłków.",
            )
