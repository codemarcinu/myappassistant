# PRAWIDŁOWA ZAWARTOŚĆ DLA PLIKU orchestrator.py

import logging
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from . import tools
from .agent_factory import AgentFactory
from .prompts import get_entity_extraction_prompt, get_intent_recognition_prompt
from .state import ConversationState
from .utils import extract_json_from_text

logger = logging.getLogger(__name__)


class IntentType(Enum):
    DODAJ_ZAKUPY = "DODAJ_ZAKUPY"
    CZYTAJ_PODSUMOWANIE = "CZYTAJ_PODSUMOWANIE"
    UPDATE_ITEM = "UPDATE_ITEM"
    DELETE_ITEM = "DELETE_ITEM"
    UPDATE_PURCHASE = "UPDATE_PURCHASE"
    DELETE_PURCHASE = "DELETE_PURCHASE"
    PROCESS_FILE = "PROCESS_FILE"
    UNKNOWN = "UNKNOWN"


class Orchestrator:
    def __init__(self, db: AsyncSession, state: ConversationState):
        self.db = db
        self.state = state
        self.agent_factory = AgentFactory()

    async def process_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Processes an uploaded file (e.g., a receipt image) using an appropriate agent."""
        # Simple factory based on file type
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            ocr_agent = self.agent_factory.create_agent("ocr")
            response = await ocr_agent.process({"file_content": file_content})
            return response.dict()
        return {"error": "Unsupported file type"}

    async def process_command(
        self, user_command: str, file_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Main entry point to process a user's text command."""
        self.state.add_message("user", user_command)
        logger.info(f"Processing command: '{user_command}'")

        if self.state.is_awaiting_clarification:
            return await self._handle_clarification(user_command)

        # Recognize intent
        intent_prompt = get_intent_recognition_prompt(user_command)
        intent_response = await tools.recognize_intent(intent_prompt)
        intent = extract_json_from_text(intent_response).get("intent", "UNKNOWN")

        if intent == "UNKNOWN":
            return {
                "response": "Nie zrozumiałem polecenia.",
                "state": self.state.to_dict(),
            }

        # Extract entities
        entity_prompt = get_entity_extraction_prompt(user_command, intent)
        entities_response = await tools.extract_entities(entity_prompt)
        entities = extract_json_from_text(entities_response)
        logger.info(f"Recognized Intent: {intent}, Entities: {entities}")

        found_objects = await tools.find_database_object(intent, entities)

        if len(found_objects) > 1:
            logger.info("Multiple objects found, asking for clarification.")
            clarification_question = tools.generate_clarification_question_text(
                options=found_objects
            )
            self.state.set_clarification_mode(
                intent=intent, entities=entities, options=found_objects
            )
            return {
                "response": clarification_question,
                "data": [obj.to_dict() for obj in found_objects],
                "state": self.state.to_dict(),
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
                success = await tools.execute_database_action(
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

                return {"response": response_text, "state": self.state.to_dict()}

            # For READ or other intents, just return the found object's data
            return {
                "response": "Znalazłem szukany wpis.",
                "data": [single_object.to_dict()],
                "state": self.state.to_dict(),
            }

        if not found_objects:
            logger.info("No objects found.")
            # For CREATE intents, this is the expected path
            if intent in ["CREATE_ITEM", "CREATE_PURCHASE"]:
                success = await tools.execute_database_action(
                    intent=intent,
                    target_object=None,
                    entities=entities,
                )
                if success:
                    return {
                        "response": "Gotowe, dodałem nowy wpis do bazy.",
                        "state": self.state.to_dict(),
                    }
                else:
                    return {
                        "response": "Nie udało mi się dodać wpisu, brakowało potrzebnych danych.",
                        "state": self.state.to_dict(),
                    }

            # For ANALYZE intents
            if intent == "ANALYZE":
                summary_data = await tools.execute_database_action(
                    intent=intent,
                    target_object=None,
                    entities=entities,
                )
                return {
                    "response": "Oto analiza Twoich wydatków.",
                    "data": summary_data,
                    "state": self.state.to_dict(),
                }

            return {
                "response": "Nie znalazłem w bazie pasujących wpisów.",
                "state": self.state.to_dict(),
            }

        # Fallback - should ideally not be reached
        return {
            "response": "Coś poszło nie tak z logiką Orchestratora.",
            "state": self.state.to_dict(),
        }

    async def _handle_clarification(self, user_command: str) -> Dict[str, Any]:
        """Handles the user's response when the agent is in clarification mode."""
        logger.info(f"Handling clarification. User response: '{user_command}'")
        # For now, a simple 'yes' confirms the first option.
        # A more robust solution would parse the user's choice.
        if "tak" in user_command.lower() or "pierwszy" in user_command.lower():
            if (
                not self.state.ambiguous_options
                or not self.state.original_intent
                or not self.state.original_entities
            ):
                self.state.reset()
                return {
                    "response": "Wystąpił błąd podczas przetwarzania odpowiedzi.",
                    "state": self.state.to_dict(),
                }

            confirmed_object = self.state.ambiguous_options[0]
            intent = self.state.original_intent
            entities = self.state.original_entities

            success = await tools.execute_database_action(
                intent=intent,
                target_object=confirmed_object,
                entities=entities,
            )
            response_text = (
                "Operacja wykonana pomyślnie."
                if success
                else "Nie udało się wykonać operacji."
            )
            self.state.reset()
            return {"response": response_text, "state": self.state.to_dict()}
        else:
            self.state.reset()
            return {
                "response": "OK, anulowałem operację.",
                "state": self.state.to_dict(),
            }


# Tworzymy instancję orkiestratora tylko w kodzie, gdzie mamy db i state!
# orchestrator = Orchestrator()
