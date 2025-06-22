import logging
import uuid
from datetime import datetime
from typing import Dict, Optional

import pybreaker

from backend.core.profile_manager import ProfileManager
from backend.core.sqlalchemy_compat import AsyncSession
from backend.models.user_profile import InteractionType

from .agent_router import AgentRouter
from .base_agent import BaseAgent
from .error_types import ErrorSeverity
from .interfaces import AgentResponse, AgentType
from .memory_manager import MemoryManager
from .orchestration_components import IntentData, MemoryContext
from .orchestrator_errors import OrchestratorError
from .response_generator import ResponseGenerator

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator implementation using dependency injection and new interfaces"""

    def __init__(
        self,
        db: AsyncSession,
        profile_manager: ProfileManager,
        intent_detector,
        agent_router: AgentRouter = None,
        memory_manager: MemoryManager = None,
        response_generator: ResponseGenerator = None,
    ):
        self.db = db
        self.profile_manager = profile_manager
        self.intent_detector = intent_detector

        # Initialize components with defaults if not provided
        self.agent_router = agent_router or AgentRouter()
        self.memory_manager = memory_manager or MemoryManager()
        self.response_generator = response_generator or ResponseGenerator()

        # Initialize default agents
        self._initialize_default_agents()

        # Circuit breaker for agent calls
        self.circuit_breaker = pybreaker.CircuitBreaker(
            fail_max=3, reset_timeout=60, name="AgentCircuitBreaker"
        )

        # Registered agents will be added via register_agent()
        self._agents: Dict[AgentType, "BaseAgent"] = {}
        self._fallback_agent: Optional["BaseAgent"] = None

    def _format_error_response(self, error: Exception) -> AgentResponse:
        """Format a standardized error response using AgentResponse"""
        if isinstance(error, (OrchestratorError, ValueError)):
            error_message = (
                str(error) or "An error occurred while processing your request"
            )
        else:
            error_message = "An error occurred while processing your request"
        return AgentResponse(
            success=False,
            error=error_message,
            severity=ErrorSeverity.HIGH.value,
            request_id=str(uuid.uuid4()),
            data={
                "error_type": type(error).__name__,
                "timestamp": datetime.now().isoformat(),
            },
        )

    async def process_file(
        self,
        file_bytes: bytes,
        filename: str,
        session_id: str,
        content_type: str,
    ) -> AgentResponse:
        """Process an uploaded file through the orchestrator"""
        try:
            # 1. Get user profile and context
            if self.profile_manager is None:
                logger.error("Profile manager is None")
                return self._format_error_response(
                    OrchestratorError("Profile manager not initialized")
                )

            await self.profile_manager.get_or_create_profile(session_id)

            if self.memory_manager is None:
                logger.error("Memory manager is None")
                return self._format_error_response(
                    OrchestratorError("Memory manager not initialized")
                )

            context = await self.memory_manager.get_context(session_id)

            # 2. Log activity
            await self.profile_manager.log_activity(
                session_id, InteractionType.FILE_UPLOAD, filename
            )

            # 3. Determine intent based on file type
            intent_type = (
                "image_processing"
                if content_type.startswith("image/")
                else (
                    "document_processing" if content_type == "application/pdf" else None
                )
            )

            if not intent_type:
                raise ValueError(f"Unsupported content type: {content_type}")

            # 4. Create intent data
            intent = IntentData(
                type=intent_type,
                entities={"filename": filename, "content_type": content_type},
            )

            # 5. Route to agent with circuit breaker
            try:
                if self.agent_router is None:
                    logger.error("Agent router is None")
                    return self._format_error_response(
                        OrchestratorError("Agent router not initialized")
                    )

                agent_response = await self.circuit_breaker.call_async(
                    self.agent_router.route_to_agent,
                    intent,
                    context,
                )

                # Add file data to context
                await self.memory_manager.update_context(
                    context,
                    {"file_processed": filename, "response": agent_response.data},
                )

                return agent_response

            except pybreaker.CircuitBreakerError as e:
                logger.error(f"Circuit breaker tripped: {e}")
                return self._format_error_response(
                    OrchestratorError("Service temporarily unavailable")
                )

        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return self._format_error_response(e)

    async def process_query(
        self,
        query: str,
        session_id: str,
        use_bielik: bool = True,
        use_perplexity: bool = False,
        **kwargs,
    ) -> AgentResponse:
        """Process user query through the agent system (alias for process_command)"""
        return await self.process_command(
            user_command=query,
            session_id=session_id,
            use_bielik=use_bielik,
            use_perplexity=use_perplexity,
            **kwargs,
        )

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        file_info: Optional[Dict] = None,
        agent_states: Optional[Dict[str, bool]] = None,
        use_perplexity: bool = False,
        use_bielik: bool = True,
    ) -> AgentResponse:
        """Process user command through the agent system"""
        try:
            # Special case for health check
            if user_command == "health_check_internal":
                return AgentResponse(
                    success=True,
                    text="Orchestrator is responsive",
                    data={"status": "ok", "message": "Orchestrator is responsive"},
                    request_id=str(uuid.uuid4()),
                )

            if not user_command:
                return AgentResponse(
                    success=False,
                    error="Empty command",
                    text="Proszę podać pytanie lub polecenie.",
                )

            # 1. Create or retrieve memory context
            context = await self.memory_manager.get_context(session_id)

            # 2. Log user activity
            await self.profile_manager.log_activity(
                session_id, InteractionType.QUERY, user_command
            )

            # 3. Detect intent
            if self.intent_detector is None:
                logger.error("Intent detector is None")
                return self._format_error_response(
                    OrchestratorError("Intent detector not initialized")
                )

            intent = await self.intent_detector.detect_intent(user_command, context)
            logger.debug(
                f"Detected intent: {intent.type} (confidence: {intent.confidence})"
            )

            # Nowa logika: Modyfikacja intencji na podstawie agent_states
            if agent_states:
                logger.info(f"Applying agent states: {agent_states}")

                # Priorytet dla trybu zakupów
                if (
                    agent_states.get("shopping")
                    and intent.type != "shopping_conversation"
                ):
                    intent.type = "shopping_conversation"
                    logger.info(
                        "Overriding intent to 'shopping_conversation' due to active toggle."
                    )

                # Priorytet dla trybu gotowania
                elif agent_states.get("cooking") and intent.type != "food_conversation":
                    intent.type = "food_conversation"
                    logger.info(
                        "Overriding intent to 'food_conversation' due to active toggle."
                    )

                # Sprawdzenie, czy wykryta intencja jest dozwolona
                is_shopping_intent = "shopping" in intent.type
                is_cooking_intent = "food" in intent.type

                if (is_shopping_intent and not agent_states.get("shopping")) or (
                    is_cooking_intent and not agent_states.get("cooking")
                ):

                    if is_shopping_intent:
                        required_mode = "Tryb Zakupów"
                    else:
                        required_mode = "Tryb Kuchenny"

                    error_message = (
                        f"Aby kontynuować, włącz {required_mode} w ustawieniach czatu."
                    )
                    logger.warning(
                        f"Intent '{intent.type}' blocked by agent_states. Message: {error_message}"
                    )
                    return AgentResponse(success=True, text=error_message)

            # 4. Route to agent with circuit breaker
            try:
                if self.agent_router is None:
                    logger.error("Agent router is None")
                    return self._format_error_response(
                        OrchestratorError("Agent router not initialized")
                    )

                try:
                    # Add a specific try-except block to catch the NameError
                    agent_response = await self.agent_router.route_to_agent(
                        intent,
                        context,
                        user_command,
                        use_perplexity,
                        use_bielik,
                    )
                except NameError as e:
                    if "gen" in str(e):
                        import traceback

                        logger.error(
                            f"NameError 'gen' caught with traceback: {traceback.format_exc()}"
                        )
                        return AgentResponse(
                            success=False,
                            error="Internal system error: Variable reference issue",
                            text="Przepraszam, wystąpił błąd wewnętrzny systemu. Zespół techniczny został powiadomiony.",
                            severity="ERROR",
                        )
                    else:
                        raise

                # 5. Update context
                await self.memory_manager.update_context(
                    context,
                    {
                        "user_command": user_command,
                        "agent_response": agent_response.data,
                    },
                )

                return agent_response

            except pybreaker.CircuitBreakerError as e:
                logger.error(f"Circuit breaker tripped: {e}")
                return self._format_error_response(
                    OrchestratorError("Service temporarily unavailable")
                )

        except NameError as e:
            if "gen" in str(e):
                logger.error(
                    f"NameError in orchestrator: {str(e)}. This is likely due to a reference to an undefined variable 'gen'."
                )
                return AgentResponse(
                    success=False,
                    error="Internal system error: Variable reference issue",
                    text="Przepraszam, wystąpił błąd wewnętrzny systemu. Zespół techniczny został powiadomiony.",
                    severity="ERROR",
                )
            else:
                logger.error(f"NameError in orchestrator: {str(e)}")
                return self._format_error_response(e)
        except Exception as e:
            logger.error(f"Error processing command: {e}")
            return self._format_error_response(e)

    def register_agent(self, agent_type: AgentType, agent: "BaseAgent") -> None:
        """Register an agent implementation"""
        if not isinstance(agent, BaseAgent):
            raise ValueError("Agent must implement BaseAgent interface")
        self.agent_router.register_agent(agent_type, agent)
        logger.info(f"Registered agent for type: {agent_type.value}")

    def set_fallback_agent(self, agent: "BaseAgent") -> None:
        """Set fallback agent for unknown intents"""
        self.agent_router.set_fallback_agent(agent)
        logger.info("Fallback agent set")

    def _initialize_default_agents(self) -> None:
        """Initialize and register default agents using dynamic imports to avoid circular dependencies"""
        try:
            # Dynamic imports to avoid circular dependencies
            from .categorization_agent import CategorizationAgent
            from .chef_agent import ChefAgent
            from .general_conversation_agent import GeneralConversationAgent
            from .ocr_agent import OCRAgent
            from .rag_agent import RAGAgent
            from .search_agent import SearchAgent
            from .weather_agent import WeatherAgent

            # Create agent instances
            self.chef_agent = ChefAgent()
            self.search_agent = SearchAgent()
            self.ocr_agent = OCRAgent()
            self.weather_agent = WeatherAgent()
            self.rag_agent = RAGAgent(name="rag_agent")
            self.general_conversation_agent = GeneralConversationAgent()
            self.categorization_agent = CategorizationAgent()

            # Register core agents
            self.register_agent(AgentType.CHEF, self.chef_agent)
            self.register_agent(AgentType.SEARCH, self.search_agent)
            self.register_agent(AgentType.OCR, self.ocr_agent)
            self.register_agent(AgentType.WEATHER, self.weather_agent)
            self.register_agent(AgentType.RAG, self.rag_agent)
            self.register_agent(AgentType.CATEGORIZATION, self.categorization_agent)
            self.register_agent(
                AgentType.GENERAL_CONVERSATION, self.general_conversation_agent
            )

            # Set GeneralConversationAgent as fallback (zamiast RAG agent)
            self.set_fallback_agent(self.general_conversation_agent)

            logger.info("Default agents initialized successfully")

        except ImportError as e:
            logger.error(f"Failed to import agent modules: {e}")
            raise OrchestratorError(f"Agent initialization failed: {e}")
        except Exception as e:
            logger.error(f"Error initializing default agents: {e}")
            raise OrchestratorError(f"Agent initialization failed: {e}")

    async def shutdown(self) -> None:
        """Clean shutdown of all components"""
        try:
            # Close any resources if needed
            pass
        except Exception as e:
            logger.error(f"Error during orchestrator shutdown: {e}")

    def _route_by_intent(self, intent_type: str, context: MemoryContext) -> "BaseAgent":
        """Route to appropriate agent based on intent type"""
        agent_type_map = {
            "weather": self.weather_agent,
            "search": self.search_agent,
            "cooking": self.chef_agent,
            "rag": self.rag_agent,
            "ocr": self.ocr_agent,
        }
        return agent_type_map.get(intent_type, self._fallback_agent)

    def _detect_intent(self, command: str, context: MemoryContext) -> str:
        """Detect intent from user command"""
        command_lower = command.lower()

        if any(word in command_lower for word in ["weather", "pogoda", "temperature"]):
            return "weather"
        elif any(word in command_lower for word in ["search", "find", "szukaj"]):
            return "search"
        elif any(
            word in command_lower for word in ["cook", "recipe", "gotuj", "przepis"]
        ):
            return "cooking"
        elif any(word in command_lower for word in ["document", "file", "dokument"]):
            return "rag"
        elif any(word in command_lower for word in ["image", "photo", "zdjęcie"]):
            return "ocr"
        else:
            return "base"

    def _determine_command_complexity(self, command: str) -> str:
        """Determine command complexity for model selection"""
        words = command.split()
        if len(words) < 3:
            return "simple"
        elif len(words) < 10:
            return "medium"
        else:
            return "complex"


# Export for direct import will be handled elsewhere to avoid circular imports
