import json
import logging
from typing import Any, AsyncGenerator, Dict

from backend.agents.base_agent import BaseAgent
from backend.agents.interfaces import AgentResponse
from backend.agents.prompts import get_meal_plan_prompt
from backend.agents.utils import extract_json_from_text
from backend.core.crud import get_available_products
from backend.core.llm_client import llm_client

logger = logging.getLogger(__name__)


class MealPlannerAgent(BaseAgent):
    def __init__(
        self,
        name: str = "MealPlannerAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name, error_handler=error_handler, fallback_manager=fallback_manager
        )

    async def process(self, context: Dict[str, Any]) -> AgentResponse:
        try:
            db = context["db"]
            available_products = await get_available_products(db)

            # Sprawdź flagę use_bielik
            use_bielik = context.get("use_bielik", True)
            model = (
                "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                if use_bielik
                else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
            )

            products_list = []
            for p in available_products:
                if hasattr(p, "name"):
                    products_list.append(
                        {"name": p.name, "quantity": getattr(p, "quantity", 1)}
                    )
                elif isinstance(p, dict) and "name" in p:
                    products_list.append(
                        {"name": p["name"], "quantity": p.get("quantity", 1)}
                    )
                else:
                    continue

            prompt = get_meal_plan_prompt(products_list)

            async def response_generator() -> AsyncGenerator[str, None]:
                full_response = ""
                try:
                    async for chunk in llm_client.generate_stream(
                        model=model,
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
                    json_str = extract_json_from_text(full_response)
                    if json_str:
                        parsed_data = json.loads(json_str)
                        logger.debug(f"Meal plan data extracted: {parsed_data}")
                    else:
                        logger.warning("No valid JSON found in meal plan response")
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
