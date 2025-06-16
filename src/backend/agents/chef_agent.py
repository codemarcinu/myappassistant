from typing import Any, Dict, List

from pydantic import BaseModel

from backend.agents.base_agent import AgentResponse, BaseAgent
from backend.agents.tools.tools import get_available_products_from_pantry
from backend.core.llm_client import llm_client


class RecipeSuggestion(BaseModel):
    """Model for recipe suggestion response"""

    recipe: str
    used_ingredients: List[Dict[str, Any]]


class ChefAgent(BaseAgent):
    """Agent that suggests recipes based on available pantry items"""

    def __init__(self, name: str = "ChefAgent"):
        super().__init__(name)

    async def process(self, input_data: Any) -> AgentResponse:
        """Main processing method - delegates to generate_recipe_idea"""
        # Check if input_data is a dict with db and model
        if isinstance(input_data, dict) and "db" in input_data:
            db = input_data.get("db")
            model = input_data.get(
                "model", "llama3"
            )  # Default to llama3 if not specified
            return await self.generate_recipe_idea(db, model)
        # For backwards compatibility
        return await self.generate_recipe_idea(input_data)

    async def generate_recipe_idea(
        self, db: Any, model: str = "llama3"
    ) -> AgentResponse:
        """
        Generates recipe ideas based on available pantry items.

        Args:
            db: Database session
            model: LLM model to use for generating the recipe (default: llama3)

        Returns:
            AgentResponse with recipe suggestion or error message
        """
        # Get available products from pantry
        products = await get_available_products_from_pantry(db)

        if not products:
            return AgentResponse(
                success=True,
                text="Twoja spiżarnia jest pusta!",
                message="Pantry is empty",
            )

        # Prepare list of available products for the prompt
        product_list = "\n".join(
            f"- {product.name} (ID: {product.id})" for product in products
        )

        # Create LLM prompt
        prompt = (
            "Mam następujące produkty w spiżarni:\n"
            f"{product_list}\n\n"
            "Proszę zaproponuj prosty przepis wykorzystujący te produkty. "
            "Odpowiedz w formacie:\n"
            "PRZEPIS: [treść przepisu]\n"
            "UŻYTE SKŁADNIKI: [lista nazw użytych składników]"
        )

        async def response_generator():
            # Call LLM with specified model and stream the response
            full_response = ""
            async for chunk in llm_client.generate_stream(
                model=model,
                messages=[
                    {"role": "system", "content": "Jesteś pomocnym szefem kuchni."},
                    {"role": "user", "content": prompt},
                ],
            ):
                content = chunk["message"]["content"]
                full_response += content
                yield content

            # After streaming, parse the full response to extract used ingredients
            used_ingredients = []
            if "UŻYTE SKŁADNIKI:" in full_response:
                parts = full_response.split("UŻYTE SKŁADNIKI:")
                ingredient_names = [
                    name.strip() for name in parts[1].split(",") if name.strip()
                ]
                used_ingredients = [
                    {"id": p.id, "name": p.name}
                    for p in products
                    if p.name in ingredient_names
                ]
            print(f"Used ingredients identified: {used_ingredients}")

        return AgentResponse(
            success=True,
            text_stream=response_generator(),
            message="Recipe stream started.",
        )
