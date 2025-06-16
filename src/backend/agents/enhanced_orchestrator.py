import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from ..core.sqlalchemy_compat import AsyncSession

from ..core.enhanced_vector_store import enhanced_vector_store
from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.memory import ConversationMemoryManager
from ..integrations.web_search import web_search_client
from ..models.conversation import Conversation, Message
from ..models.user_profile import InteractionType, ProfileManager
from .agent_factory import AgentFactory
from .enhanced_base_agent import EnhancedAgentResponse, ErrorSeverity, ImprovedBaseAgent
from .enhanced_weather_agent import EnhancedWeatherAgent

logger = logging.getLogger(__name__)


class EnhancedOrchestrator:
    """
    Upgraded orchestrator that integrates all enhanced components:
    - Long-term memory for contextual conversations
    - Optimized RAG with smart chunking
    - Web search for fresh information
    - Enhanced weather data with multi-provider fallback
    - User profiling and personalization
    - Cost-effective model selection
    - Robust error handling and fallbacks
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.agent_factory = AgentFactory()
        self.profile_manager = ProfileManager(db)
        self.memory_managers: Dict[str, ConversationMemoryManager] = {}

        # Initialize enhanced weather agent
        self.weather_agent = EnhancedWeatherAgent()

        # Pre-register specialized agents
        self._register_enhanced_agents()

    def _register_enhanced_agents(self) -> None:
        """Register enhanced agents with the factory"""
        # Register the enhanced weather agent
        self.agent_factory.register_agent("enhanced_weather", self.weather_agent)

    async def _get_memory_manager(
        self, session_id: str, conversation: Optional[Conversation] = None
    ) -> ConversationMemoryManager:
        """Get or create memory manager for session"""
        if session_id not in self.memory_managers:
            memory_manager = ConversationMemoryManager(session_id)
            self.memory_managers[session_id] = memory_manager

            # Initialize from conversation history if provided
            if conversation:
                await memory_manager.initialize_from_history(conversation)

        return self.memory_managers[session_id]

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        file_info: Optional[Dict] = None,
        agent_states: Optional[Dict[str, bool]] = None,
    ) -> Dict[str, Any]:
        """
        Main entry point to process a user's command with all enhancements
        """
        start_time = datetime.now()

        try:
            # 1. Get user profile for personalization
            user_profile = await self.profile_manager.get_or_create_profile(session_id)

            # 2. Get conversation and memory manager
            from ..core import crud

            conversation = await crud.get_conversation_by_session_id(
                self.db, session_id
            )
            if not conversation:
                conversation = await crud.create_conversation(self.db, session_id)

            memory_manager = await self._get_memory_manager(session_id, conversation)

            # 3. Log user interaction for analytics
            await self.profile_manager.log_activity(
                session_id, InteractionType.QUERY, user_command
            )

            # 4. Get personalized suggestions if command is very short (likely greeting)
            personalized_context = ""
            if len(user_command) < 15:
                suggestions = await self.profile_manager.get_personalized_suggestions(
                    session_id
                )
                if suggestions:
                    personalized_context = f"Sugestie:\n" + "\n".join(
                        f"- {s}" for s in suggestions[:2]
                    )

            # 5. Determine model based on query complexity and active agents
            complexity_level = await self._determine_command_complexity(user_command)

            # Override complexity based on agent states if needed
            if agent_states:
                if agent_states.get("shopping", False) or agent_states.get(
                    "cooking", False
                ):
                    # These specific domains may need more complex reasoning
                    complexity_level = ModelComplexity.COMPLEX

            # 6. Get relevant memory context
            memory_context = await memory_manager.retrieve_context(user_command)
            memory_text = ""
            if memory_context:
                memory_items = [f"- {ctx['content']}" for ctx in memory_context]
                memory_text = "Kontekst z wcześniejszych rozmów:\n" + "\n".join(
                    memory_items
                )

            # 7. Detect intent to determine appropriate agent
            intent_data = await self._detect_intent(
                user_command, personalized_context, memory_text, complexity_level
            )

            # Add message to conversation history
            await crud.create_message(self.db, conversation.id, "user", user_command)

            # 8. Route to appropriate handler based on intent
            response = await self._route_by_intent(
                user_command,
                intent_data,
                session_id,
                complexity_level,
                agent_states or {},
                personalized_context,
                memory_text,
            )

            # 9. Update memory with the interaction
            await memory_manager.add_message("user", user_command)
            if "response" in response:
                await memory_manager.add_message("assistant", response["response"])

            # 10. Calculate and log processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Processed command in {processing_time:.2f}s (intent: {intent_data.get('intent', 'unknown')})"
            )

            # Add processing metadata to response
            response["metadata"] = {
                "processing_time": processing_time,
                "intent": intent_data.get("intent"),
                "complexity_level": complexity_level.value,
                "personalized": bool(personalized_context),
            }

            return response

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return {
                "response": "Wystąpił błąd podczas przetwarzania polecenia. Proszę spróbować ponownie.",
                "error": str(e),
            }

    async def _determine_command_complexity(self, command: str) -> ModelComplexity:
        """Determine the complexity level of a command"""
        # Use the hybrid client's complexity analysis
        messages = [{"role": "user", "content": command}]
        complexity, _, _ = await hybrid_llm_client._get_complexity_level(messages)
        return complexity

    async def _detect_intent(
        self,
        command: str,
        personalized_context: str,
        memory_context: str,
        complexity_level: ModelComplexity,
    ) -> Dict[str, Any]:
        """Detect user intent with context awareness"""
        # Construct prompt with available context
        context_parts = []
        if personalized_context:
            context_parts.append(personalized_context)
        if memory_context:
            context_parts.append(memory_context)

        context_text = "\n\n".join(context_parts)

        prompt = f"""Przeanalizuj intencję użytkownika w poniższym zapytaniu:

Zapytanie: "{command}"

{context_text}

Określ główną intencję z poniższych kategorii:
- WEATHER: Zapytanie o pogodę lub warunki atmosferyczne
- SEARCH: Ogólne wyszukiwanie informacji
- RAG: Zapytanie o wiedzę zgromadzoną w dokumentach
- COOKING: Zapytanie związane z gotowaniem, przepisami lub planowaniem posiłków
- SHOPPING: Zapytanie związane z zakupami lub zarządzaniem produktami
- CHAT: Konwersacja ogólna lub small talk
- UNKNOWN: Intencja nie pasuje do żadnej z powyższych kategorii

Odpowiedz w formacie JSON:
{{
  "intent": "NAZWA_INTENCJI",
  "confidence": 0.0-1.0,
  "entities": [],
  "requires_clarification": false
}}
"""

        # Select model based on complexity
        model = (
            "gemma2:2b" if complexity_level == ModelComplexity.SIMPLE else "gemma3:12b"
        )

        response = await hybrid_llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś asystentem analizującym intencje użytkownika.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            force_complexity=complexity_level,
        )

        # Extract JSON from response
        if response and "message" in response:
            content = response["message"]["content"]

            # Find JSON content (simple implementation)
            import json
            import re

            json_match = re.search(r"({.*})", content, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(1).strip()
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError) as e:
                    logger.error(f"Error parsing intent JSON: {e}")

        # Fallback if parsing fails
        return {
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "entities": [],
            "requires_clarification": False,
        }

    async def _route_by_intent(
        self,
        command: str,
        intent_data: Dict[str, Any],
        session_id: str,
        complexity_level: ModelComplexity,
        agent_states: Dict[str, bool],
        personalized_context: str,
        memory_context: str,
    ) -> Dict[str, Any]:
        """Route command to appropriate handler based on intent"""
        intent = intent_data.get("intent", "UNKNOWN")
        logger.info(f"Routing command to handler for intent: {intent}")

        # Handle clarification if needed
        if intent_data.get("requires_clarification", False):
            return await self._handle_clarification(command, intent_data, session_id)

        # Route based on intent
        if intent == "WEATHER" and agent_states.get("weather", True):
            return await self._handle_weather(command, session_id, complexity_level)

        elif intent == "SEARCH" and agent_states.get("search", True):
            return await self._handle_search(command, session_id, complexity_level)

        elif intent == "RAG":
            return await self._handle_rag(command, session_id, complexity_level)

        elif intent == "COOKING" and agent_states.get("cooking", False):
            return await self._handle_cooking(command, session_id, complexity_level)

        elif intent == "SHOPPING" and agent_states.get("shopping", False):
            return await self._handle_shopping(command, session_id, complexity_level)

        else:
            # Default to general chat with context
            return await self._handle_general_chat(
                command,
                session_id,
                complexity_level,
                personalized_context,
                memory_context,
            )

    async def _handle_clarification(
        self, command: str, intent_data: Dict[str, Any], session_id: str
    ) -> Dict[str, Any]:
        """Handle requests requiring clarification"""
        # This would implement ambiguity resolution logic
        # For now, just return a message asking for clarification
        options = intent_data.get("ambiguous_options", [])
        options_text = "\n".join([f"- {opt}" for opt in options]) if options else ""

        return {
            "response": f"Przepraszam, nie jestem pewien, o co dokładnie pytasz. Czy możesz doprecyzować?\n\n{options_text}",
            "requires_clarification": True,
            "original_intent": intent_data.get("intent"),
            "options": options,
        }

    async def _handle_weather(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle weather-related queries with enhanced weather agent"""
        logger.info(f"Handling weather query: {command}")

        # Use enhanced weather agent
        try:
            # Process with our multi-provider weather agent
            agent_response = await self.weather_agent.process(
                {
                    "query": command,
                    "model": "gemma3:12b",  # Override with consistent model
                    "include_alerts": True,
                }
            )

            # If streaming response is available, return it
            if agent_response.text_stream:
                return {
                    "response": "Przetwarzanie prognozy pogody...",
                    "text_stream": agent_response.text_stream,
                    "data": agent_response.data,
                }

            # Otherwise, return static response
            return {
                "response": agent_response.text
                or agent_response.message
                or "Prognoza pogody przetworzona pomyślnie.",
                "data": agent_response.data,
            }

        except Exception as e:
            logger.error(f"Error processing weather query: {e}")
            return {
                "response": "Wystąpił błąd podczas pobierania danych pogodowych. Proszę spróbować ponownie."
            }

    async def _handle_search(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle search queries with web search integration"""
        logger.info(f"Handling search query: {command}")

        try:
            # Extract search query (simplified version)
            search_terms = (
                command.replace("wyszukaj", "")
                .replace("znajdź", "")
                .replace("szukaj", "")
                .strip()
            )

            # If search terms are too short, ask for clarification
            if len(search_terms) < 3:
                return {
                    "response": "Proszę podać bardziej szczegółowe zapytanie do wyszukania.",
                    "requires_clarification": True,
                }

            # Perform web search
            search_response = await web_search_client.search(search_terms)

            # Check if we got any results
            if not search_response.results:
                return {
                    "response": f"Niestety, nie znalazłem żadnych informacji na temat '{search_terms}'.",
                    "data": {"query": search_terms, "results": []},
                }

            # Prepare results for LLM processing
            results_text = "\n\n".join(
                [
                    f"Tytuł: {result.title}\nŹródło: {result.source}\nOpis: {result.snippet}"
                    for result in search_response.results[:5]
                ]
            )

            # Generate response using LLM
            prompt = f"""Na podstawie poniższych wyników wyszukiwania, utwórz zwięzłą i pomocną odpowiedź na zapytanie użytkownika.

Zapytanie: "{search_terms}"

Wyniki wyszukiwania:
{results_text}

Odpowiedź powinna być w języku polskim, dobrze ustrukturyzowana i zawierać najważniejsze informacje z wyników.
"""

            response = await hybrid_llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który tworzy zwięzłe podsumowania wyników wyszukiwania.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="gemma3:12b",
                force_complexity=ModelComplexity.STANDARD,
            )

            # Extract response text
            if response and "message" in response:
                answer = response["message"]["content"]

                # Return formatted response
                return {
                    "response": answer,
                    "data": {
                        "query": search_terms,
                        "results": [
                            result.dict() for result in search_response.results
                        ],
                    },
                }

            # Fallback
            return {
                "response": f"Znalazłem informacje na temat '{search_terms}', ale nie mogę ich teraz przetworzyć.",
                "data": {"query": search_terms, "results": []},
            }

        except Exception as e:
            logger.error(f"Error processing search query: {e}")
            return {
                "response": "Wystąpił błąd podczas wyszukiwania. Proszę spróbować ponownie."
            }

    async def _handle_rag(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle RAG queries using enhanced vector store"""
        logger.info(f"Handling RAG query: {command}")

        try:
            # Search the vector store
            results = await enhanced_vector_store.search(
                query=command, k=5, min_similarity=0.65
            )

            if not results:
                # No relevant documents found, fall back to general chat
                return await self._handle_general_chat(
                    command,
                    session_id,
                    complexity_level,
                    "",
                    "Nie znalazłem odpowiednich dokumentów w bazie wiedzy.",
                )

            # Prepare context from results
            context = "\n\n".join(
                [
                    f"FRAGMENT {i+1}:\n{result['text']}"
                    for i, result in enumerate(results)
                ]
            )

            # Generate response using LLM
            prompt = f"""Na podstawie poniższych fragmentów dokumentów, odpowiedz na zapytanie użytkownika.

Zapytanie: "{command}"

Kontekst:
{context}

Udziel wyczerpującej odpowiedzi w języku polskim, opierając się na dostarczonych fragmentach. Jeśli fragmenty nie zawierają potrzebnych informacji, przyznaj to uczciwie.
"""

            response = await hybrid_llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem, który odpowiada na pytania w oparciu o dostarczone dokumenty.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model="gemma3:12b",
                force_complexity=ModelComplexity.COMPLEX,
            )

            # Extract response text
            if response and "message" in response:
                answer = response["message"]["content"]

                # Return formatted response
                return {
                    "response": answer,
                    "data": {"query": command, "document_count": len(results)},
                }

            # Fallback
            return {
                "response": "Znalazłem dokumenty, które mogą być pomocne, ale nie mogę ich teraz przetworzyć.",
                "data": {"query": command, "document_count": len(results)},
            }

        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            return {
                "response": "Wystąpił błąd podczas przeszukiwania bazy wiedzy. Proszę spróbować ponownie."
            }

    async def _handle_cooking(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle cooking-related queries"""
        logger.info(f"Handling cooking query: {command}")

        # Get cooking agent from factory and process
        try:
            cooking_agent = self.agent_factory.create_agent("chef")
            agent_response = await cooking_agent.process(
                {
                    "query": command,
                    "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q6_K",  # Use specialized model
                    "session_id": session_id,
                }
            )

            return {
                "response": agent_response.text
                or "Zapytanie kulinarne przetworzone pomyślnie.",
                "data": agent_response.data,
            }
        except Exception as e:
            logger.error(f"Error processing cooking query: {e}")
            return {
                "response": "Wystąpił błąd podczas przetwarzania zapytania kulinarnego. Proszę spróbować ponownie."
            }

    async def _handle_shopping(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle shopping-related queries"""
        logger.info(f"Handling shopping query: {command}")

        # This would implement shopping agent logic
        # For now, return a placeholder
        return {
            "response": "Przepraszam, funkcjonalność zakupowa jest obecnie w trakcie rozwoju."
        }

    async def _handle_general_chat(
        self,
        command: str,
        session_id: str,
        complexity_level: ModelComplexity,
        personalized_context: str,
        memory_context: str,
    ) -> Dict[str, Any]:
        """Handle general chat queries with personalization and memory"""
        logger.info(f"Handling general chat: {command}")

        # Build context for LLM
        context_parts = []
        if personalized_context:
            context_parts.append(personalized_context)
        if memory_context:
            context_parts.append(memory_context)

        context_text = "\n\n".join(context_parts)

        # Select model based on complexity
        model = "llama3:8b"
        if complexity_level == ModelComplexity.SIMPLE:
            model = "gemma2:2b"
        elif complexity_level == ModelComplexity.COMPLEX:
            model = "gemma3:12b"
        elif complexity_level == ModelComplexity.CRITICAL:
            model = "llama3:70b"

        # Generate response using appropriate model
        prompt = f"""Użytkownik: {command}

{context_text}"""

        response = await hybrid_llm_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś pomocnym, przyjaznym asystentem, który odpowiada po polsku.",
                },
                {"role": "user", "content": prompt},
            ],
            model=model,
            force_complexity=complexity_level,
        )

        # Extract response text
        if response and "message" in response:
            answer = response["message"]["content"]

            # Return formatted response
            return {
                "response": answer,
                "model_used": model,
                "complexity": complexity_level.value,
            }

        # Fallback
        return {
            "response": "Przepraszam, nie mogę teraz przetworzyć tego zapytania.",
            "model_used": model,
            "complexity": complexity_level.value,
        }

    async def shutdown(self) -> None:
        """Clean shutdown of all components"""
        try:
            # Close weather agent HTTP client
            if hasattr(self.weather_agent, "close") and callable(
                self.weather_agent.close
            ):
                await self.weather_agent.close()

            # Close web search client
            await web_search_client.close()

        except Exception as e:
            logger.error(f"Error during orchestrator shutdown: {e}")


# Export for direct import
enhanced_orchestrator = None  # Will be initialized with DB session
