# w pliku backend/agents/food_save_agent.py

import json
from datetime import date, timedelta
from typing import Dict, Any, Optional

from .base_agent import BaseAgent, AgentResponse
from ..core.llm_client import ollama_client
from ..config import settings
from ..services import shopping_service
from ..schemas import shopping_schemas
from ..core.database import AsyncSessionLocal


class FoodSaveAgent(BaseAgent):
    """
    Agent do zarządzania zakupami, który potrafi zapisywać i odczytywać dane.
    """
    def __init__(self):
        super().__init__(
            name="FoodSaveAgent",
            description="Zarządza danymi o zakupach, produktach spożywczych, przepisach i datach ważności."
        )

    async def _handle_add_trip(self, task_description: str) -> AgentResponse:
        """Obsługuje logikę dodawania nowego paragonu."""
        self.logger.info("Intencja: ZAPIS. Uruchamiam proces ekstrakcji danych.")
        
        # Ten prompt jest taki sam jak w poprzednim kroku
        json_format_instructions = """
        {"trip_date": "YYYY-MM-DD", "store_name": "Nazwa Sklepu", "products": [{"name": "Nazwa Produktu", "quantity": 1.0, "unit_price": 10.50}]}
        """
        prompt = f"""
        Jesteś precyzyjnym asystentem do wprowadzania danych. Twoim zadaniem jest przetworzenie poniższego tekstu opisującego zakupy i przekształcenie go w strukturę JSON.
        - Jeśli użytkownik wspomina o dniu dzisiejszym, użyj daty: {date.today().isoformat()}.
        - Jeśli użytkownik wspomina o dniu wczorajszym, użyj daty: {(date.today() - timedelta(days=1)).isoformat()}.
        - Zawsze zwracaj tylko i wyłącznie kod JSON, bez żadnych dodatkowych wyjaśnień.

        Tekst do przetworzenia: --- {task_description} ---
        Oczekiwany format JSON: {json_format_instructions}
        """
        
        try:
            full_response = ""
            async for chunk in ollama_client.generate_stream(model=settings.DEFAULT_CODE_MODEL, prompt=prompt):
                if "response" in chunk: full_response += chunk["response"]
            
            cleaned_json_str = full_response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned_json_str)
            trip_data = shopping_schemas.ShoppingTripCreate(**data)
        except Exception as e:
            self.logger.error(f"Błąd przetwarzania odpowiedzi LLM lub walidacji danych: {e}")
            return AgentResponse(success=False, result=None, error=f"Błąd przetwarzania polecenia przez LLM: {e}")

        try:
            async with AsyncSessionLocal() as db_session:
                created_trip = await shopping_service.create_shopping_trip(db=db_session, trip=trip_data)
            response_data = shopping_schemas.ShoppingTrip.model_validate(created_trip)
            self.logger.info(f"Pomyślnie dodano paragon o ID: {response_data.id}")
            return AgentResponse(success=True, result=response_data.model_dump())
        except Exception as e:
            self.logger.error(f"Błąd zapisu do bazy danych: {e}")
            return AgentResponse(success=False, result=None, error=f"Błąd zapisu do bazy danych: {e}")

    async def _handle_read_trips(self, task_description: str) -> AgentResponse:
        """Obsługuje logikę odczytywania paragonów i tworzenia podsumowania."""
        self.logger.info("Intencja: ODCZYT. Pobieram dane z bazy.")
        try:
            # Ta funkcja pomocnicza 'nauczy' bibliotekę json, jak obsługiwać daty
            def json_date_serializer(obj):
                if isinstance(obj, date):
                    return obj.isoformat()
                raise TypeError(f"Type {type(obj)} not serializable")

            async with AsyncSessionLocal() as db_session:
                trips = await shopping_service.get_shopping_trips(db=db_session, limit=5)
            
            if not trips:
                return AgentResponse(success=True, result="Nie znalazłem żadnych zapisanych paragonów.")

            trips_data = [shopping_schemas.ShoppingTrip.model_validate(t).model_dump(exclude={'id', 'products.id', 'products.trip_id'}) for t in trips]
            
            summary_prompt = f"""
            Jesteś pomocnym asystentem zakupowym. Twoim zadaniem jest zwięzłe i czytelne podsumowanie poniższych danych o zakupach w języku polskim.
            Odpowiedz w formie naturalnej, przyjaznej konwersacji. Nie używaj formatowania Markdown.

            Dane o zakupach (JSON):
            {json.dumps(trips_data, indent=2, ensure_ascii=False, default=json_date_serializer)}

            Twoje podsumowanie:
            """
            full_response = ""
            async for chunk in ollama_client.generate_stream(model=settings.DEFAULT_CODE_MODEL, prompt=summary_prompt):
                if "response" in chunk: full_response += chunk["response"]

            return AgentResponse(success=True, result=full_response)
        except Exception as e:
            self.logger.error(f"Błąd odczytu lub podsumowania paragonów: {e}")
            return AgentResponse(success=False, result=None, error=f"Błąd odczytu danych: {e}")

    async def execute(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Główna metoda agenta - najpierw klasyfikuje intencję, potem deleguje zadanie."""
        self.logger.info(f"FoodSaveAgent otrzymał zadanie: '{task_description}'")

        intent_prompt = f"""
        Przeanalizuj poniższe polecenie użytkownika i określ jego intencję. Odpowiedz jednym słowem: ZAPIS lub ODCZYT.
        Przykłady dla 'ZAPIS': 'dodaj paragon', 'zapisz nowe zakupy', 'właśnie wróciłem z Biedronki'.
        Przykłady dla 'ODCZYT': 'pokaż ostatnie', 'co kupiłem ostatnio?', 'wyświetl paragony'.

        Polecenie: "{task_description}"
        Intencja:
        """
        
        intent_response = ""
        async for chunk in ollama_client.generate_stream(model=settings.DEFAULT_CODE_MODEL, prompt=intent_prompt):
            if "response" in chunk: intent_response += chunk["response"]

        intent = intent_response.strip().upper()
        self.logger.info(f"Wykryta intencja: {intent}")

        if 'ZAPIS' in intent:
            return await self._handle_add_trip(task_description)
        elif 'ODCZYT' in intent:
            return await self._handle_read_trips(task_description)
        else:
            self.logger.warning(f"Nie udało się jednoznacznie określić intencji: {intent}")
            return AgentResponse(success=False, result=None, error="Nie udało mi się zrozumieć polecenia. Sprecyzuj, czy chcesz coś dodać, czy odczytać.")

# Ta linia pozostaje bez zmian
food_save_agent = FoodSaveAgent()