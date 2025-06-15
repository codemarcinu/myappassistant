import logging
import re
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession  # type: ignore

from backend.agents.agent_factory import AgentFactory
from backend.agents.prompts import (
    get_entity_extraction_prompt,
    get_intent_recognition_prompt,
)
from backend.agents.state import ConversationState, append_to_history, get_agent_state
from backend.agents.tools.date_parser import parse_date_range_with_llm
from backend.agents.tools.tools import (
    execute_database_action,
    extract_entities,
    find_database_object,
    generate_clarification_question_text,
    recognize_intent,
)
from backend.agents.utils import extract_json_from_text
from backend.core import crud
from backend.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class IntentType(Enum):
    DODAJ_ZAKUPY = "DODAJ_ZAKUPY"
    CZYTAJ_PODSUMOWANIE = "CZYTAJ_PODSUMOWANIE"
    UPDATE_ITEM = "UPDATE_ITEM"
    DELETE_ITEM = "DELETE_ITEM"
    UPDATE_PURCHASE = "UPDATE_PURCHASE"
    DELETE_PURCHASE = "DELETE_PURCHASE"
    PROCESS_FILE = "PROCESS_FILE"
    COOKING = "COOKING"
    MARK_PRODUCTS_CONSUMED = "MARK_PRODUCTS_CONSUMED"
    UNKNOWN = "UNKNOWN"


class Orchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_factory = AgentFactory()

    async def process_file(
        self, file_content: bytes, filename: str, session_id: str
    ) -> Dict[str, Any]:
        """Processes an uploaded file (e.g., a receipt image) using an appropriate agent."""
        # Simple factory based on file type
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            ocr_agent = self.agent_factory.create_agent("ocr")
            ocr_response = await ocr_agent.process({"file_content": file_content})

            # Integrate the OCR response into the conversation
            ocr_text = ocr_response.text
            user_command = (
                f"Przetworzono plik '{filename}'. Rozpoznany tekst: {ocr_text}"
            )
            return await self.process_command(user_command, session_id)

        return {"error": "Unsupported file type"}

    async def process_command(
        self, user_command: str, session_id: str, file_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Main entry point to process a user's text command."""
        state = get_agent_state(session_id)
        state.add_message("user", user_command)
        logger.info(f"Processing command: '{user_command}' for session: {session_id}")

        if state.is_awaiting_clarification:
            return await self._handle_clarification(user_command, state)

        # Recognize intent
        intent_prompt = get_intent_recognition_prompt(user_command)
        intent_response = await recognize_intent(intent_prompt)
        intent = extract_json_from_text(intent_response).get("intent", "UNKNOWN")

        # Check for cooking-related phrases if intent is UNKNOWN
        if intent == "UNKNOWN":
            cooking_phrases = [
                "co mogę ugotować",
                "zaproponuj przepis",
                "co zrobić z",
                "pomysł na obiad",
                "przepis na",
            ]
            if any(phrase in user_command.lower() for phrase in cooking_phrases):
                intent = "COOKING"

        if intent == "UNKNOWN":
            return {
                "response": "Nie zrozumiałem polecenia.",
                "state": state.to_dict(),
            }

        # Extract entities
        entity_prompt = get_entity_extraction_prompt(user_command, intent)
        entities_response = await extract_entities(entity_prompt)
        entities = extract_json_from_text(entities_response)
        logger.info(f"Recognized Intent: {intent}, Entities: {entities}")

        found_objects = await find_database_object(self.db, intent, entities)

        if len(found_objects) > 1:
            logger.info("Multiple objects found, asking for clarification.")
            clarification_question = generate_clarification_question_text(
                options=found_objects
            )
            state.set_clarification_mode(
                intent=intent, entities=entities, options=found_objects
            )
            return {
                "response": clarification_question,
                "data": [obj.to_dict() for obj in found_objects],
                "state": state.to_dict(),
            }
        elif len(found_objects) == 1:
            logger.info("Single object found, proceeding with action.")
            single_object = found_objects[0]

            # Check if the intent is for modification (UPDATE/DELETE)
            modification_intents = [
                "UPDATE_ITEM",
                "DELETE_ITEM",
                "UPDATE_PURCHASE",
                "DELETE_PURCHASE",
            ]
            if intent in modification_intents:
                success = await execute_database_action(
                    db=self.db,
                    intent=intent,
                    target_object=single_object,
                    entities=entities,
                )
                if success:
                    action_word = (
                        "Zaktualizowałem" if "UPDATE" in intent else "Usunąłem"
                    )
                    response_text = f"{action_word} wpis."
                else:
                    response_text = "Wystąpił błąd podczas modyfikacji danych."

                return {"response": response_text, "state": state.to_dict()}

            # For READ or other intents, just return the found object's data
            return {
                "response": "Znalazłem szukany wpis.",
                "data": [single_object.to_dict()],
                "state": state.to_dict(),
            }

        if not found_objects:
            logger.info("No objects found.")
            # For CREATE intents, this is the expected path
            if intent in ["CREATE_ITEM", "CREATE_PURCHASE", "DODAJ_ZAKUPY"]:
                success = await execute_database_action(
                    db=self.db,
                    intent=intent,
                    target_object=None,
                    entities=entities,
                )
                if success:
                    return {
                        "response": "Gotowe, dodałem nowy wpis do bazy.",
                        "state": state.to_dict(),
                    }
                else:
                    return {
                        "response": "Nie udało mi się dodać wpisu, brakowało potrzebnych danych.",
                        "state": state.to_dict(),
                    }

            # Handle cooking intent
            if intent == "COOKING":
                chef_agent = self.agent_factory.create_agent("chef")
                chef_response = await chef_agent.process(self.db)

                if not chef_response.success or not chef_response.data:
                    return {
                        "response": "Nie udało się wygenerować przepisu.",
                        "state": state.to_dict(),
                    }

                try:
                    recipe = chef_response.data.get("recipe", "")
                    used_ingredients = chef_response.data.get("used_ingredients", [])

                    if not recipe or not used_ingredients:
                        return {
                            "response": "Nie udało się wygenerować przepisu.",
                            "state": state.to_dict(),
                        }

                    # Store used ingredients in state for confirmation
                    state.set_cooking_state(used_ingredients)

                    return {
                        "response": f"{recipe}\n\nCzy przygotowałeś to danie? To pozwoli mi zaktualizować stan spiżarni.",
                        "state": state.to_dict(),
                    }
                except (KeyError, AttributeError):
                    return {
                        "response": "Wystąpił błąd podczas przetwarzania przepisu.",
                        "state": state.to_dict(),
                    }

            # Handle cooking confirmation
            if state.is_cooking_confirmation and "tak" in user_command.lower():
                # Mark ingredients as consumed
                success = await execute_database_action(
                    db=self.db,
                    intent="MARK_PRODUCTS_CONSUMED",
                    target_object=None,
                    entities={"ingredients": state.cooking_ingredients},
                )

                state.reset()

                return {
                    "response": (
                        "Świetnie! Zaktualizowałem stan spiżarni o zużyte składniki."
                        if success
                        else "Nie udało się zaktualizować stanu spiżarni."
                    ),
                    "state": state.to_dict(),
                }

            # For ANALYZE intents
            if intent == "ANALYZE":
                summary_data = await execute_database_action(
                    db=self.db,
                    intent=intent,
                    target_object=None,
                    entities=entities,
                )
                return {
                    "response": "Oto analiza Twoich wydatków.",
                    "data": summary_data,
                    "state": state.to_dict(),
                }

            return {
                "response": "Nie znalazłem w bazie pasujących wpisów.",
                "state": state.to_dict(),
            }

        # Fallback - should ideally not be reached
        return {
            "response": "Coś poszło nie tak z logiką Orchestratora.",
            "state": state.to_dict(),
        }

    async def _handle_clarification(
        self, user_command: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Handles the user's response when the agent is in clarification mode."""
        logger.info(f"Handling clarification. User response: '{user_command}'")

        # Try to parse a number from the user's command
        try:
            # Find the first number in the string
            match = re.search(r"\d+", user_command)
            if not match:
                raise ValueError("No number found in user response")
            choice_idx = int(match.group(0)) - 1

            if not (0 <= choice_idx < len(state.ambiguous_options)):
                raise IndexError("Choice is out of bounds")

            if not state.original_intent or not state.original_entities:
                raise ValueError("Incomplete state for clarification")

            confirmed_object = state.ambiguous_options[choice_idx]
            intent = state.original_intent
            entities = state.original_entities

            success = await execute_database_action(
                db=self.db,
                intent=intent,
                target_object=confirmed_object,
                entities=entities,
            )
            response_text = (
                "Operacja wykonana pomyślnie."
                if success
                else "Nie udało się wykonać operacji."
            )
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not parse user's clarification choice: {e}")
            response_text = (
                "Nie zrozumiałem wyboru. Proszę, podaj numer opcji. Anuluję operację."
            )

        state.reset()
        return {"response": response_text, "state": state.to_dict()}

    async def get_agent_response_with_date_parsing(
        self, user_message: str, session_id: str
    ) -> Dict[str, Any]:
        """
        Processes a user message, using conversation memory and date parsing tools.
        """
        # 1. Add user message to history
        append_to_history(session_id, {"role": "user", "content": user_message})

        # 2. Get current conversation state
        current_state = get_agent_state(session_id)
        history = current_state.history

        date_range = parse_date_range_with_llm(user_message)

        if date_range:
            start_dt = date.fromisoformat(date_range["start_date"])
            end_dt = date.fromisoformat(date_range["end_date"])

            trips = await crud.get_trips_by_date_range(
                self.db, start_date=start_dt, end_date=end_dt
            )

            if not trips:
                agent_response_text = f"Nie znalazłem żadnych zakupów w okresie od {start_dt} do {end_dt}."
            else:
                response_lines = [
                    f"Znalazłem {len(trips)} wypraw na zakupy w podanym okresie:"
                ]
                for trip in trips:
                    response_lines.append(
                        f"- {trip.trip_date}: {trip.store_name} za {trip.total_amount or 0:.2f} zł"
                    )
                agent_response_text = "\n".join(response_lines)
        else:
            agent_response_text = f"Nie znalazłem w Twojej wiadomości informacji o dacie. Powiedziałeś: '{user_message}'."

        # 5. Add agent's response to history
        append_to_history(
            session_id, {"role": "assistant", "content": agent_response_text}
        )

        return {"response": agent_response_text, "history_length": len(history)}


async def get_memory_agent_response(
    user_message: str, session_id: str
) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej.
    """
    # 1. Dodaj nową wiadomość użytkownika do historii
    append_to_history(session_id, {"role": "user", "content": user_message})

    # 2. Pobierz aktualny stan konwersacji (już z nową wiadomością)
    current_state = get_agent_state(session_id)
    history = current_state.history

    # TODO: W tym miejscu w przyszłości umieścimy logikę LLM.
    agent_response_text = (
        f"Zapamiętałem, że napisałeś: '{user_message}'. "
        f"Łączna liczba wiadomości w historii: {len(history)}."
    )

    # 3. Dodaj odpowiedź agenta do historii
    append_to_history(session_id, {"role": "assistant", "content": agent_response_text})

    return {"response": agent_response_text, "history_length": len(history)}


async def get_agent_response(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej i narzędzi.
    """
    # Ta funkcja jest teraz wrapperem, który tworzy sesję i wywołuje metodę Orchestratora
    async with AsyncSessionLocal() as db:
        orchestrator = Orchestrator(db)
        return await orchestrator.process_command(user_message, session_id)
