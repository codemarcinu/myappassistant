import logging
import re
from collections import OrderedDict
from datetime import datetime
from typing import Any, Dict, Optional

from ..core.enhanced_vector_store import EnhancedVectorStore
from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.memory import ConversationMemoryManager
from ..core.profile_manager import ProfileManager
from ..core.sqlalchemy_compat import AsyncSession
from ..integrations.web_search import web_search_client
from ..models.conversation import Conversation
from ..models.user_profile import InteractionType
from .orchestrator_errors import (
    AgentProcessingError,
    IntentRecognitionError,
    MemoryManagerError,
    OrchestratorError,
    ProfileManagerError,
    ServiceUnavailableError,
)

logger = logging.getLogger(__name__)

# Moved imports to avoid circular dependencies


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

    def __init__(
        self,
        db: AsyncSession,
        agent_factory: AgentFactory,
        profile_manager: ProfileManager,
        router_service: RouterService,
        weather_agent: EnhancedWeatherAgent,
        # Add other dependencies as needed
    ):
        self.db = db
        self.agent_factory = agent_factory
        self.profile_manager = profile_manager
        self.memory_managers: OrderedDict[str, ConversationMemoryManager] = (
            OrderedDict()
        )
        self.max_memory_managers = (
            1000  # Maximum number of memory managers to keep in cache
        )
        self.router = router_service
        self.weather_agent = weather_agent

        # Pre-register specialized agents
        self._register_enhanced_agents()

    def _register_enhanced_agents(self) -> None:
        """Register enhanced agents with the factory"""
        # Register the enhanced weather agent
        self.agent_factory.register_agent("enhanced_weather", self.weather_agent)

    async def _get_memory_manager(
        self, session_id: str, conversation: Optional[Conversation] = None
    ) -> ConversationMemoryManager:
        """Get or create memory manager for session with LRU caching"""
        # If exists, move to end (most recently used) and return
        if session_id in self.memory_managers:
            manager = self.memory_managers[session_id]
            # Move to end by removing and reinserting
            del self.memory_managers[session_id]
            self.memory_managers[session_id] = manager
            return manager

        # Create new manager
        manager = ConversationMemoryManager(session_id)
        # Add to cache
        self.memory_managers[session_id] = manager

        # If cache is full, remove the least recently used (first item)
        if len(self.memory_managers) > self.max_memory_managers:
            oldest_session_id = next(iter(self.memory_managers))
            del self.memory_managers[oldest_session_id]

        # Initialize from history if provided
        if conversation:
            await manager.initialize_from_history(conversation)

        return manager

    def _format_error_response(self, error: Exception) -> Dict[str, Any]:
        """Format a standardized error response"""
        error_type = type(error).__name__
        error_message = str(error) or "Wystąpił nieznany błąd"
        user_message = "Przepraszam, wystąpił błąd podczas przetwarzania żądania. Proszę spróbować ponownie."

        if isinstance(error, AgentProcessingError):
            user_message = "Błąd przetwarzania agenta: " + error_message
        elif isinstance(error, ServiceUnavailableError):
            user_message = "Usługa jest obecnie niedostępna. Spróbuj ponownie później."
        elif isinstance(error, IntentRecognitionError):
            user_message = (
                "Nie udało się rozpoznać intencji komendy. Spróbuj wyrazić ją inaczej."
            )
        elif isinstance(error, MemoryManagerError):
            user_message = "Błąd zarządzania pamięcią konwersacji."
        elif isinstance(error, ProfileManagerError):
            user_message = "Błąd zarządzania profilem użytkownika."

        return {
            "response": user_message,
            "status": "error",
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat(),
        }

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
            await self.profile_manager.get_or_create_profile(session_id)

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
                    personalized_context = "Sugestie:\n" + "\n".join(
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
                "Processed command in %.2fs (intent: %s)",
                processing_time,
                intent_data.get("intent", "unknown"),
            )

            # Add processing metadata to response
            response["metadata"] = {
                "processing_time": processing_time,
                "intent": intent_data.get("intent"),
                "complexity_level": complexity_level.value,
                "personalized": bool(personalized_context),
            }

            return response

        except OrchestratorError as e:
            logger.error(f"Orchestrator specific error: {e}")
            return self._format_error_response(e)
        except Exception as e:
            logger.error(f"Unexpected error processing command: {e}")
            return self._format_error_response(e)

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
        return await self.router.detect_intent(
            command=command,
            personalized_context=personalized_context,
            memory_context=memory_context,
            complexity_level=complexity_level,
        )

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
        if intent_data.get("requires_clarification", False):
            return await self._handle_clarification(command, intent_data, session_id)

        return await self.router.route_command(
            command=command,
            intent_data=intent_data,
            session_id=session_id,
            complexity_level=complexity_level,
            agent_states=agent_states,
            personalized_context=personalized_context,
            memory_context=memory_context,
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
                    "model": "SpeakLeash/bielik-11b-v2.3-instruct:Q8_0",  # Override with consistent model
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
            # Improved query extraction using regex to handle natural language queries
            search_terms = command
            patterns = [
                r"wyszukaj\s+(.+)",
                r"znajdź\s+(.+)",
                r"szukaj\s+(.+)",
                r"wyszukiwanie\s+(.+)",
                r"znalezienie\s+(.+)",
                r"poszukaj\s+(.+)",
            ]

            # Try to match extraction patterns
            for pattern in patterns:
                match = re.search(pattern, command, re.IGNORECASE)
                if match:
                    search_terms = match.group(1).strip()
                    break

            # If no pattern matched, use the whole command
            if search_terms == command:
                logger.info(
                    f"No search pattern matched, using entire command as search terms: {command}"
                )

            # Validate search terms
            if len(search_terms) < 2:
                return {
                    "response": "Proszę podać bardziej szczegółowe zapytanie do wyszukania.",
                    "requires_clarification": True,
                }

            # Remove question marks if they're at the end
            if search_terms.endswith("?"):
                search_terms = search_terms[:-1].strip()

            # Perform web search with enhanced validation
            if not search_terms or len(search_terms) > 200:
                logger.warning(f"Invalid search terms: '{search_terms}'")
                return {
                    "response": "Nieprawidłowe zapytanie wyszukiwania. Proszę spróbować ponownie.",
                    "status": "error",
                }

            # Perform web search
            try:
                search_response = await web_search_client.search(search_terms)
            except Exception as e:
                logger.error(f"Web search failed: {e}")
                return {
                    "response": "Wystąpił problem z wyszukiwaniem. Proszę spróbować ponownie później.",
                    "status": "error",
                }

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
                model="SpeakLeash/bielik-11b-v2.3-instruct:Q8_0",
                force_complexity=ModelComplexity.STANDARD,
            )

            # Extract response text
            if response and "message" in response:
                answer = response["message"]["content"]

                # Return formatted response
            return {
                "response": answer,
                "status": "success",
                "data": {
                    "query": search_terms,
                    "results": [result.dict() for result in search_response.results],
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
                "response": "Wystąpił błąd podczas wyszukiwania. Proszę spróbować ponownie.",
                "status": "error",
            }

    async def _handle_rag(
        self, command: str, session_id: str, complexity_level: ModelComplexity
    ) -> Dict[str, Any]:
        """Handle RAG queries using enhanced vector store"""
        logger.info(f"Handling RAG query: {command}")

        try:
            # Search the vector store
            vector_store = EnhancedVectorStore()
            results = await vector_store.search(query=command, k=5, min_similarity=0.65)

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
                model="SpeakLeash/bielik-11b-v2.3-instruct:Q8_0",
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

        # Select model based on complexity - force gemma3:latest for general chat
        model = "gemma3:latest"
        if complexity_level == ModelComplexity.SIMPLE:
            model = "gemma:2b"

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

    async def remove_memory_manager(self, session_id: str) -> None:
        """Explicitly remove a memory manager by session_id"""
        if session_id in self.memory_managers:
            del self.memory_managers[session_id]

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


# Export for direct import will be handled elsewhere to avoid circular imports
