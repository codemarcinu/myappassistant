import logging
import re
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents.agent_factory import AgentFactory
from backend.agents.prompts import (
    get_entity_extraction_prompt,
    get_intent_recognition_prompt,
)
from backend.agents.state import ConversationState
from backend.agents.tools.date_parser import parse_date_range_with_llm
from backend.agents.tools.tools import (
    execute_database_action,
    extract_entities,
    find_database_object,
    generate_clarification_question_text,
    get_current_date,
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
    MEAL_PLAN = "MEAL_PLAN"
    ANALYZE = "ANALYZE"
    RAG = "RAG"
    UNKNOWN = "UNKNOWN"


class Orchestrator:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_factory = AgentFactory()

    async def process_file(
        self, file_bytes: bytes, filename: str, session_id: str, content_type: str
    ) -> Dict[str, Any]:
        """Processes an uploaded file (e.g., a receipt image) using an appropriate agent."""
        file_type = "image" if content_type.startswith("image/") else "pdf"

        ocr_agent = self.agent_factory.create_agent("ocr")
        ocr_response = await ocr_agent.process(
            {"file_bytes": file_bytes, "file_type": file_type}
        )

        if not ocr_response.success:
            return {"error": ocr_response.error or "Failed to process file with OCR."}

        # Integrate the OCR response into the conversation
        ocr_text = ocr_response.text
        user_command = f"Przetworzono plik '{filename}'. Rozpoznany tekst: {ocr_text}"
        return await self.process_command(user_command, session_id)

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        file_info: Optional[Dict] = None,
        agent_states: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """Main entry point to process a user's text command."""
        conversation = await crud.get_conversation_by_session_id(self.db, session_id)
        if not conversation:
            conversation = await crud.create_conversation(self.db, session_id)

        await crud.add_message_to_conversation(
            self.db, conversation.id, "user", user_command
        )

        state = ConversationState(session_id=session_id)
        # TODO: Load state from conversation history
        logger.info(f"Processing command: '{user_command}' for session: {session_id}")

        # Store agent states in conversation state
        if agent_states:
            state.agent_states = agent_states
            logger.info(f"Active agents: {agent_states}")

        # Set appropriate model based on active agents
        if state.agent_states.get("shopping", False) or state.agent_states.get(
            "cooking", False
        ):
            state.current_model = "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K"
            logger.info(
                f"Using Polish model for shopping/cooking: {state.current_model}"
            )
        else:
            state.current_model = "gemma3:12b"
            logger.info(f"Using default model: {state.current_model}")

        # --- Start of Refactored Logic ---

        # High-priority keyword-based routing for specific agents
        if state.agent_states.get("weather", True) and self._is_weather_query(
            user_command
        ):
            logger.info(f"Routing to Weather Agent for: '{user_command}'")
            return await self._process_weather_query(user_command, state)

        if state.agent_states.get("search", True) and self._is_search_query(
            user_command
        ):
            logger.info(f"Routing to Search Agent for: '{user_command}'")
            return await self._process_search_query(user_command, state)

        if state.agent_states.get("cooking", False) and self._is_cooking_query(
            user_command
        ):
            logger.info(f"Routing to Chef Agent for: '{user_command}'")
            return await self._process_cooking_query(user_command, state)

        if self._is_meal_plan_query(user_command):
            logger.info(f"Routing to Meal Planner Agent for: '{user_command}'")
            return await self._process_meal_plan_query(user_command, state)

        if self._is_analyze_query(user_command):
            logger.info(f"Routing to Analytics Agent for: '{user_command}'")
            return await self._process_analyze_query(user_command, state)

        if self._is_date_query(user_command):
            logger.info(f"Routing to Date Tool for: '{user_command}'")
            date_response = get_current_date()
            return {"response": date_response, "state": state.to_dict()}

        # --- Fallback to Intent Recognition Logic ---

        logger.info("No specific agent triggered, falling back to intent recognition.")

        # 1. Recognize Intent
        intent_prompt = get_intent_recognition_prompt(user_command)
        intent_response = await recognize_intent(intent_prompt)
        intent_data = extract_json_from_text(intent_response)
        intent = intent_data.get("intent", "UNKNOWN")
        logger.info(f"Recognized Intent: {intent}")

        # 2. Extract Entities
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

    async def _process_general_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """
        Processes a general query using an LLM to decide which tool to use.
        This replaces the keyword-based if/elif chain.
        """
        from backend.agents.prompts import get_react_prompt

        react_prompt = get_react_prompt(query)

        from backend.core.llm_client import llm_client

        try:
            response = await llm_client.chat(
                model=state.current_model,
                messages=[{"role": "user", "content": react_prompt}],
                stream=False,
                options={"temperature": 0.0},
            )

            if not response or not response.get("message"):
                raise ValueError("Invalid response from LLM")

            tool_choice_str = response["message"]["content"]
            tool_choice = extract_json_from_text(tool_choice_str)

            tool_name = tool_choice.get("tool")
            tool_input = tool_choice.get("tool_input", query)

            logger.info(
                f"LLM decided to use tool: {tool_name} with input: {tool_input}"
            )

            if tool_name == "weather":
                return await self._process_weather_query(tool_input, state)
            elif tool_name == "search":
                return await self._process_search_query(tool_input, state)
            elif tool_name == "rag":
                return await self._process_rag_query(tool_input, state)
            else:  # Default to a conversational response
                return {
                    "response": "Nie bardzo rozumiem, czy możesz doprecyzować?",
                    "state": state.to_dict(),
                }

        except Exception as e:
            logger.error(f"Error processing general query with ReAct prompt: {e}")
            return {
                "response": "Przepraszam, mam problem z przetworzeniem Twojego zapytania.",
                "state": state.to_dict(),
            }

    def _is_weather_query(self, query: str) -> bool:
        """Check if this is a weather-related query"""
        weather_keywords = [
            "pogoda",
            "deszcz",
            "temperatura",
            "stopni",
            "śnieg",
            "burza",
            "słońce",
            "zachmurzenie",
            "ciepło",
            "zimno",
            "chłodno",
            "upał",
            "prognoza",
            "meteorolog",
        ]
        return any(keyword in query.lower() for keyword in weather_keywords)

    def _is_search_query(self, query: str) -> bool:
        """Check if this is a search query"""
        search_keywords = [
            "wyszukaj",
            "znajdź",
            "szukaj",
            "poszukaj",
            "google",
            "internet",
            "informacje o",
            "co to jest",
            "kto to jest",
            "gdzie jest",
            "kiedy",
            "jak",
        ]
        return any(keyword in query.lower() for keyword in search_keywords)

    def _is_cooking_query(self, query: str) -> bool:
        """Check if this is a cooking-related query"""
        cooking_keywords = [
            "przepis",
            "ugotuj",
            "upiec",
            "przygotować",
            "danie",
            "obiad",
            "kolacja",
            "śniadanie",
            "jedzenie",
            "posiłek",
            "kuchnia",
            "gotowanie",
            "smażenie",
            "pieczenie",
            "dusić",
        ]
        return any(keyword in query.lower() for keyword in cooking_keywords)

    def _is_shopping_query(self, query: str) -> bool:
        """Check if this is a shopping-related query"""
        shopping_keywords = [
            "zakupy",
            "kupić",
            "sklep",
            "promocja",
            "cena",
            "produkt",
            "artykuł",
            "spożywczy",
            "warzywa",
            "owoce",
            "nabiał",
            "mięso",
            "pieczywo",
            "paragon",
            "lista zakupów",
        ]
        return any(keyword in query.lower() for keyword in shopping_keywords)

    def _is_meal_plan_query(self, query: str) -> bool:
        """Check if this is a meal plan-related query"""
        meal_plan_keywords = [
            "zaplanuj posiłki",
            "plan posiłków",
            "co na obiad",
            "co na kolację",
            "co na śniadanie",
            "jadłospis",
        ]
        return any(keyword in query.lower() for keyword in meal_plan_keywords)

    async def _process_meal_plan_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a meal plan query using the meal planner agent"""
        try:
            meal_planner_agent = self.agent_factory.create_agent("meal_planner")
            response = await meal_planner_agent.process({"db": self.db})

            if response.success and response.text_stream:
                return response.text_stream
            else:
                return {
                    "response": response.error
                    or "Wystąpił problem z planowaniem posiłków.",
                    "state": state.to_dict(),
                }
        except Exception as e:
            logger.error(f"Error processing meal plan query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z planowaniem posiłków.",
                "state": state.to_dict(),
            }

    def _is_analyze_query(self, query: str) -> bool:
        """Check if this is an analyze-related query"""
        analyze_keywords = [
            "analizuj",
            "podsumuj",
            "pokaż wydatki",
            "ile wydałem",
            "statystyki",
        ]
        return any(keyword in query.lower() for keyword in analyze_keywords)

    async def _process_analyze_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process an analyze query using the analytics agent"""
        try:
            analytics_agent = self.agent_factory.create_agent("analytics")
            # TODO: Extract query params from the query
            response = await analytics_agent.process(
                {"db": self.db, "query_params": {}}
            )

            if response.success:
                return {
                    "response": response.text,
                    "data": response.data,
                    "state": state.to_dict(),
                }
            else:
                return {
                    "response": response.error or "Wystąpił problem z analizą danych.",
                    "state": state.to_dict(),
                }
        except Exception as e:
            logger.error(f"Error processing analyze query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z analizą danych.",
                "state": state.to_dict(),
            }

    def _is_date_query(self, query: str) -> bool:
        """Check if this is a date-related query."""
        date_keywords = [
            "który dzisiaj",
            "jaki jest dzień",
            "jaka jest data",
            "dzień tygodnia",
            "dzisiaj jest",
        ]
        return any(keyword in query.lower() for keyword in date_keywords)

    def _is_rag_query(self, query: str) -> bool:
        """Check if this is a RAG-related query"""
        rag_keywords = [
            "co to jest",
            "wyjaśnij",
            "powiedz mi o",
            "czym jest",
        ]
        return any(keyword in query.lower() for keyword in rag_keywords)

    async def _process_rag_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a RAG query using the RAG agent"""
        try:
            rag_agent = self.agent_factory.create_agent("rag")
            response = await rag_agent.process({"query": query})

            if response.success:
                return {
                    "response": response.text,
                    "data": response.data,
                    "state": state.to_dict(),
                }
            else:
                return {
                    "response": response.error
                    or "Wystąpił problem z odpowiedzią na pytanie.",
                    "state": state.to_dict(),
                }
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z odpowiedzią na pytanie.",
                "state": state.to_dict(),
            }

    async def _process_weather_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a weather query using the weather agent"""
        logger.info(f"Processing weather query: '{query}'")

        try:
            # Create and call the weather agent
            weather_agent = self.agent_factory.create_agent("weather")
            logger.info("Weather agent created successfully, processing query")

            response = await weather_agent.process(
                {"query": query, "model": state.current_model}
            )
            logger.info(f"Weather agent response: {response}")

            # Check for successful response
            if response.success and response.text_stream:
                logger.info("Weather query successful, returning stream.")
                # The response is the stream itself
                return response.text_stream
            else:
                error_msg = (
                    response.error or "Wystąpił problem z uzyskaniem prognozy pogody."
                )
                logger.error(f"Weather agent returned error: {error_msg}")

                # Add error message to conversation history
                state.add_message("assistant", str(error_msg))

                return {
                    "response": error_msg,
                    "state": state.to_dict(),
                }
        except Exception as e:
            error_msg = (
                f"Przepraszam, wystąpił problem z uzyskaniem prognozy pogody: {str(e)}"
            )
            logger.error(f"Exception in weather processing: {e}", exc_info=True)

            # Add error message to conversation history
            state.add_message("assistant", str(error_msg))

            return {
                "response": error_msg,
                "state": state.to_dict(),
            }

    async def _process_search_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a search query using the search agent"""
        try:
            search_agent = self.agent_factory.create_agent("search")
            response = await search_agent.process(
                {"query": query, "model": state.current_model}
            )

            if response.success and response.text_stream:
                return response.text_stream
            else:
                return {
                    "response": response.error
                    or "Wystąpił problem z wyszukiwaniem informacji.",
                    "state": state.to_dict(),
                }
        except Exception as e:
            logger.error(f"Error processing search query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z wyszukiwaniem informacji.",
                "state": state.to_dict(),
            }

    async def _process_cooking_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a cooking query using the chef agent with Polish model"""
        try:
            # Create chef agent
            chef_agent = self.agent_factory.create_agent("chef")

            # Store the current model to use for processing
            model_to_use = state.current_model
            logger.info(f"Using model for cooking: {model_to_use}")

            # Pass the model information through database context
            chef_context = {"db": self.db, "model": model_to_use}

            # Process with chef agent
            response = await chef_agent.process(chef_context)

            if response.success and response.text_stream:
                return response.text_stream
            else:
                return {
                    "response": response.error
                    or "Wystąpił problem z generowaniem przepisu.",
                    "state": state.to_dict(),
                }
        except Exception as e:
            logger.error(f"Error processing cooking query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z generowaniem przepisu.",
                "state": state.to_dict(),
            }

    async def _process_shopping_query(
        self, query: str, state: ConversationState
    ) -> Dict[str, Any]:
        """Process a shopping query using Polish model"""
        try:
            # For shopping, we use standard intent recognition but with Polish model
            prompt = get_intent_recognition_prompt(query)

            # Use the Polish model directly
            from backend.core.llm_client import llm_client

            intent_response = await llm_client.chat(
                model=state.current_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem zakupowym.",
                    },
                    {"role": "user", "content": prompt},
                ],
                stream=False,
            )

            # Extract the response content
            if intent_response and "message" in intent_response:
                intent_content = intent_response["message"]["content"]
            else:
                intent_content = "Nie rozumiem polecenia związanego z zakupami."

            # Process the shopping intent
            return {
                "response": intent_content,
                "state": state.to_dict(),
            }
        except Exception as e:
            logger.error(f"Error processing shopping query: {e}")
            return {
                "response": "Przepraszam, wystąpił problem z przetwarzaniem zapytania o zakupy.",
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
        conversation = await crud.get_conversation_by_session_id(self.db, session_id)
        if not conversation:
            conversation = await crud.create_conversation(self.db, session_id)
        await crud.add_message_to_conversation(
            self.db, conversation.id, "user", user_message
        )

        # 2. Get current conversation state
        # TODO: This should be loaded from the conversation history
        current_state = ConversationState(session_id=session_id)
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
        await crud.add_message_to_conversation(
            self.db, conversation.id, "assistant", agent_response_text
        )

        return {"response": agent_response_text, "history_length": len(history)}


async def get_memory_agent_response(
    user_message: str, session_id: str
) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej.
    """
    async with AsyncSessionLocal() as db:
        conversation = await crud.get_conversation_by_session_id(db, session_id)
        if not conversation:
            conversation = await crud.create_conversation(db, session_id)

        await crud.add_message_to_conversation(
            db, conversation.id, "user", user_message
        )

        # TODO: W tym miejscu w przyszłości umieścimy logikę LLM.
        agent_response_text = (
            f"Zapamiętałem, że napisałeś: '{user_message}'. "
            f"Łączna liczba wiadomości w historii: {len(conversation.messages)}."
        )

        await crud.add_message_to_conversation(
            db, conversation.id, "assistant", agent_response_text
        )

        return {
            "response": agent_response_text,
            "history_length": len(conversation.messages),
        }


async def get_agent_response(user_message: str, session_id: str) -> Dict[str, Any]:
    """
    Główna funkcja, która przetwarza wiadomość użytkownika,
    korzystając z pamięci konwersacyjnej i narzędzi.
    """
    # Ta funkcja jest teraz wrapperem, który tworzy sesję i wywołuje metodę Orchestratora
    async with AsyncSessionLocal() as db:
        orchestrator = Orchestrator(db)
        return await orchestrator.process_command(user_message, session_id)
