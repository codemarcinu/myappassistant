# PRAWIDŁOWA ZAWARTOŚĆ DLA PLIKU orchestrator.py

import logging
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from .agent_factory import AgentFactory
from .prompts import (get_entity_extraction_prompt,
                      get_intent_recognition_prompt)
from .state import ConversationState, append_to_history, get_agent_state
from .tools.tools import (execute_database_action, extract_entities,
                          find_database_object,
                          generate_clarification_question_text,
                          recognize_intent)
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
            response = await ocr_agent.process({"file_content": file_content})
            # TODO: Process the OCR response and integrate it into the conversation state
            return response.dict()
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

        found_objects = await find_database_object(intent, entities)

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
            if intent in ["CREATE_ITEM", "CREATE_PURCHASE"]:
                success = await execute_database_action(
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

            # For ANALYZE intents
            if intent == "ANALYZE":
                summary_data = await execute_database_action(
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
        # For now, a simple 'yes' confirms the first option.
        # A more robust solution would parse the user's choice.
        if "tak" in user_command.lower() or "pierwszy" in user_command.lower():
            if (
                not state.ambiguous_options
                or not state.original_intent
                or not state.original_entities
            ):
                state.reset()
                return {
                    "response": "Wystąpił błąd podczas przetwarzania odpowiedzi.",
                    "state": state.to_dict(),
                }

            confirmed_object = state.ambiguous_options[0]
            intent = state.original_intent
            entities = state.original_entities

            success = await execute_database_action(
                intent=intent,
                target_object=confirmed_object,
                entities=entities,
            )
            response_text = (
                "Operacja wykonana pomyślnie."
                if success
                else "Nie udało się wykonać operacji."
            )
            state.reset()
            return {"response": response_text, "state": state.to_dict()}
        else:
            state.reset()
            return {
                "response": "OK, anulowałem operację.",
                "state": state.to_dict(),
            }


# Tworzymy instancję orkiestratora tylko w kodzie, gdzie mamy db i state!
# orchestrator = Orchestrator()


async def get_memory_agent_response(
    user_message: str, session_id: str
) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej.

    Ta funkcja używa nowej pamięci konwersacyjnej zaimplementowanej w state.py,
    działając niezależnie od klasy Orchestrator.
    """
    # 1. Dodaj nową wiadomość użytkownika do historii
    from .state import append_to_history, get_agent_state

    append_to_history(session_id, {"role": "user", "content": user_message})

    # 2. Pobierz aktualny stan konwersacji (już z nową wiadomością)
    current_state = get_agent_state(session_id)
    history = current_state.history

    # --- Logika Agenta (na razie prosta) ---
    # TODO: W tym miejscu w przyszłości umieścimy logikę LLM,
    # która przeanalizuje całą historię i wygeneruje inteligentną odpowiedź.
    # Na razie, dla testu, stworzymy prostą odpowiedź potwierdzającą.

    print(f"--- Pełna historia dla sesji '{session_id}' ---")
    for message in history:
        print(f"- {message['role']}: {message['content']}")
    print("------------------------------------")

    agent_response_text = (
        f"Zapamiętałem, że napisałeś: '{user_message}'. "
        f"Łączna liczba wiadomości w historii: {len(history)}."
    )
    # --- Koniec Logiki Agenta ---

    # 3. Dodaj odpowiedź agenta do historii
    append_to_history(session_id, {"role": "assistant", "content": agent_response_text})

    return {"response": agent_response_text, "history_length": len(history)}


async def get_agent_response(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej i narzędzi.
    """
    # 1. Dodaj wiadomość użytkownika do historii
    append_to_history(session_id, {"role": "user", "content": user_message})

    # 2. Pobierz aktualny stan konwersacji
    current_state = get_agent_state(session_id)
    history = current_state.history

    # --- Logika Agenta ---

    # Importujemy narzędzie do parsowania dat
    from .tools.date_parser import parse_date_range_with_llm

    # 3. Spróbuj użyć narzędzia do parsowania daty
    date_range = parse_date_range_with_llm(user_message)

    # 4. Wygeneruj odpowiedź na podstawie wyniku
    if date_range:
        agent_response_text = f"Zrozumiałem, że pytasz o okres od {date_range['start_date']} do {date_range['end_date']}. Wkrótce będę umiał pobrać dane dla tego zakresu!"
    else:
        # Wyświetlamy historię w konsoli dla debugowania
        print(f"--- Pełna historia dla sesji '{session_id}' ---")
        for message in history:
            print(f"- {message['role']}: {message['content']}")
        print("------------------------------------")

        agent_response_text = f"Nie znalazłem w Twojej wiadomości informacji o dacie. Powiedziałeś: '{user_message}'."

    # --- Koniec Logiki Agenta ---

    # 5. Dodaj odpowiedź agenta do historii
    append_to_history(session_id, {"role": "assistant", "content": agent_response_text})

    return {"response": agent_response_text, "history_length": len(history)}
