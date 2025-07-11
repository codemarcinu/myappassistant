from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..core.llm_client import llm_client
from .base_agent import BaseAgent
from .interfaces import AgentResponse
from .tools.tools import get_available_products_from_pantry


class ChefAgentInput(BaseModel):
    """Input model for ChefAgent"""

    available_ingredients: List[str] = Field(
        default_factory=list, min_length=1, description="List of available ingredients"
    )
    dietary_restrictions: Optional[str] = Field(
        None, description="Dietary restrictions"
    )
    model: Optional[str] = Field(
        "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0", description="LLM model to use"
    )


class RecipeSuggestion(BaseModel):
    """Model for recipe suggestion response"""

    recipe: str
    used_ingredients: List[Dict[str, Any]]


class ChefAgent(BaseAgent):
    """Agent that suggests recipes based on available pantry items"""

    def __init__(
        self,
        name: str = "ChefAgent",
        error_handler: Any = None,
        fallback_manager: Any = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name,
            error_handler=error_handler,
            fallback_manager=fallback_manager,
            **kwargs,
        )
        self.input_model = ChefAgentInput
        self.llm_client = llm_client  # Dodaję atrybut llm_client dla testów

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """Main processing method - validates input and generates recipe"""
        try:
            # Sprawdź flagę use_bielik
            use_bielik = input_data.get("use_bielik", True)
            model = (
                "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                if use_bielik
                else "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
            )

            # Aktualizuj input_data z wybranym modelem
            input_data["model"] = model

            # Validate input
            validated_input = ChefAgentInput.model_validate(input_data)

            # Generate recipe
            return await self._generate_recipe(
                ingredients=validated_input.available_ingredients,
                dietary_restrictions=validated_input.dietary_restrictions,
                model=validated_input.model
                or "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                text=f"Przepraszam, wystąpił błąd: {str(e)}",
            )

    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata including capabilities"""
        return {
            "name": self.name,
            "type": "chef",
            "capabilities": ["recipe_generation", "ingredient_analysis"],
            "description": "Generates recipes based on available ingredients",
        }

    def get_dependencies(self) -> List[type]:
        """List of agent types this agent depends on"""
        return []

    def is_healthy(self) -> bool:
        """Check if agent is functioning properly"""
        return True

    async def _generate_recipe(
        self,
        ingredients: List[str],
        dietary_restrictions: Optional[str] = None,
        model: str = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
    ) -> AgentResponse:
        """Generate recipe from given ingredients"""
        if not ingredients:
            return AgentResponse(
                success=False,
                error="No ingredients provided",
                text="Proszę podać składniki",
            )

        # Prepare prompt
        prompt = (
            "Mam następujące składniki:\n"
            f"{', '.join(ingredients)}\n\n"
            "Proszę zaproponuj prosty przepis wykorzystujący te składniki."
        )

        if dietary_restrictions:
            prompt += f"\n\nUwzględnij następujące ograniczenia dietetyczne: {dietary_restrictions}"

        async def recipe_generator() -> None:
            try:
                # Call LLM with streaming
                response = await self.llm_client.chat(
                    model=model,
                    messages=[
                        {"role": "system", "content": "Jesteś pomocnym szefem kuchni."},
                        {"role": "user", "content": prompt},
                    ],
                    stream=True,
                )

                # Stream the response chunks
                full_response = ""
                async for chunk in response:
                    content = chunk["message"]["content"]
                    full_response += content
                    yield content

            except Exception as e:
                yield f"Przepraszam, wystąpił błąd: {str(e)}"

        return AgentResponse(
            success=True,
            text="Recipe generation started",
            text_stream=recipe_generator(),
            message="Recipe generation started",
        )

    async def generate_recipe_idea(
        self, db: Any, model: str = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
    ) -> AgentResponse:
        """
        Generates recipe ideas based on available pantry items.

        Args:
            db: Database session
            model: LLM model to use for generating the recipe (default: SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0)

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

        async def response_generator() -> None:
            # Call LLM with specified model and stream the response
            full_response = ""
            async for chunk in await self.llm_client.generate_stream(
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
