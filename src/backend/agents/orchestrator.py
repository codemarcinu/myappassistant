import logging
import uuid
from datetime import datetime
from typing import Any, Callable, Coroutine, Dict, Optional

import pybreaker
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.profile_manager import ProfileManager
from backend.models.user_profile import InteractionType

from .agent_router import AgentRouter
from .base_agent import BaseAgent
from .error_types import ErrorSeverity
from .intent_detector import SimpleIntentDetector as IntentDetector
from .interfaces import AgentResponse, AgentType
from .memory_manager import MemoryManager
from .orchestrator_errors import OrchestratorError
from .response_generator import ResponseGenerator

logger = logging.getLogger(__name__)


class SimpleCircuitBreaker:
    """
    Simple CircuitBreaker for protecting asynchronous calls
    without using problematic pybreaker library
    """

    # State constants
    STATE_CLOSED = "closed"
    STATE_OPEN = "open"
    STATE_HALF_OPEN = "half-open"

    def __init__(self, name: str, fail_max: int = 3, reset_timeout: int = 60) -> None:
        """Initialize Circuit Breaker"""
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.current_state = self.STATE_CLOSED
        self.failures = 0
        self.last_failure_time = 0
        logger.info(
            f"Initialized SimpleCircuitBreaker({name}) with fail_max={fail_max}, reset_timeout={reset_timeout}"
        )

    async def call_async(
        self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any
    ) -> Any:
        """Execute async function with circuit breaker protection"""
        current_time = datetime.now().timestamp()

        # Check if circuit is open and if reset timeout has passed
        if self.current_state == self.STATE_OPEN:
            if current_time - self.last_failure_time > self.reset_timeout:
                logger.info(
                    f"CircuitBreaker({self.name}) reset timeout expired, moving to half-open"
                )
                self.current_state = self.STATE_HALF_OPEN
            else:
                logger.warning(f"CircuitBreaker({self.name}) is OPEN, rejecting call")
                raise pybreaker.CircuitBreakerError(
                    f"CircuitBreaker {self.name} is OPEN. Try again later."
                )

        try:
            # Call the function
            result = await func(*args, **kwargs)

            # Success - reset failure counter
            if self.current_state in [self.STATE_CLOSED, self.STATE_HALF_OPEN]:
                self.failures = 0
                self.current_state = self.STATE_CLOSED

            return result

        except Exception as e:
            # Handle error
            self.failures += 1
            self.last_failure_time = current_time

            logger.warning(
                f"CircuitBreaker({self.name}) recorded failure {self.failures}/{self.fail_max}: {str(e)}"
            )

            # If failure limit exceeded, open the circuit
            if self.failures >= self.fail_max:
                self.current_state = self.STATE_OPEN
                logger.error(f"CircuitBreaker({self.name}) is now OPEN")

            # Re-raise the error
            raise


class Orchestrator:
    """Main orchestrator implementation using dependency injection and new interfaces"""

    def __init__(
        self,
        db_session: Optional[AsyncSession] = None,
        profile_manager: Optional[ProfileManager] = None,
        intent_detector: Optional[IntentDetector] = None,
        agent_router: Optional[AgentRouter] = None,
        memory_manager: Optional[MemoryManager] = None,
        response_generator: Optional[ResponseGenerator] = None,
    ) -> None:
        self.db = db_session
        self.profile_manager = profile_manager or ProfileManager(db_session)
        self.intent_detector = intent_detector or IntentDetector()
        self.agent_router = agent_router or AgentRouter()
        self.memory_manager = memory_manager or MemoryManager()
        self.response_generator = response_generator or ResponseGenerator()

        # Initialize circuit breaker
        self.circuit_breaker = SimpleCircuitBreaker(
            name="AgentCircuitBreaker", fail_max=3, reset_timeout=60
        )

        # Registered agents will be added via register_agent()
        self._agents: Dict[AgentType, "BaseAgent"] = {}
        self._fallback_agent: Optional["BaseAgent"] = None

    def _initialize_default_agents(self) -> None:
        """Initialize default agents - now properly implemented"""
        logger.info("Initializing default agents")
        try:
            # This method is now properly implemented but agents are injected via factory
            # The actual agent initialization happens in AgentFactory
            logger.info(
                "Default agent initialization completed via dependency injection"
            )
        except Exception as e:
            logger.error(f"Error initializing default agents: {e}")

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
                    user_command=filename,
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
        self, query: str, session_id: str, **kwargs: Any
    ) -> AgentResponse:
        """Process user query through the agent system."""
        return await self.process_command(
            user_command=query, session_id=session_id, **kwargs
        )

    async def process_command(
        self,
        user_command: str,
        session_id: str,
        stream: bool = False,
        stream_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        agent_states: Optional[Dict[str, bool]] = None,
        use_perplexity: bool = False,
        use_bielik: bool = True,
    ) -> AgentResponse:
        """Process user command through the agent system"""
        request_id = str(uuid.uuid4())
        logger.info(
            f"[Request ID: {request_id}] Received command: '{user_command}' for session: {session_id}"
        )

        try:
            # 1. Get user profile and context
            context = await self.memory_manager.get_context(session_id)
            context.last_command = user_command
            context.request_id = request_id

            # 2. Log activity
            await self.profile_manager.log_activity(
                session_id, InteractionType.QUERY, user_command
            )

            # 3. Detect intent
            intent = await self.intent_detector.detect_intent(user_command, context)

            # 4. Route to agent with circuit breaker
            try:
                agent_response = await self.circuit_breaker.call_async(
                    self.agent_router.route_to_agent,
                    intent,
                    context,
                    user_command=user_command,
                )
            except pybreaker.CircuitBreakerError as e:
                logger.error(f"Circuit breaker tripped for intent {intent.type}: {e}")
                return self._format_error_response(
                    OrchestratorError(
                        "Service temporarily unavailable due to repeated errors.",
                        severity=ErrorSeverity.HIGH.value,
                    )
                )

            # 5. Update context with agent's response
            await self.memory_manager.update_context(
                context, {"last_response": agent_response}
            )

            logger.info(
                f"[Request ID: {request_id}] Successfully processed command with agent response"
            )
            return agent_response

        except OrchestratorError as e:
            logger.error(
                f"[Request ID: {request_id}] Orchestrator error: {e}", exc_info=True
            )
            return self._format_error_response(e)
        except Exception as e:
            logger.error(
                f"[Request ID: {request_id}] Unhandled error: {e}", exc_info=True
            )
            return self._format_error_response(
                OrchestratorError(f"An unexpected error occurred: {e}")
            )

    async def shutdown(self) -> None:
        """Perform graceful shutdown of orchestrator components."""
        logger.info("Orchestrator shutdown initiated.")
        # Example: close database connection if it was opened by orchestrator
        if self.db:
            await self.db.close()
        # Add any other cleanup logic here
        logger.info("Orchestrator shutdown completed.")

    def _determine_command_complexity(self, command: str) -> str:
        """Determine command complexity (e.g., 'simple', 'medium', 'complex')."""
        if len(command) < 20:
            return "simple"
        elif len(command) < 100:
            return "medium"
        else:
            return "complex"

    def _initialize_agents(self) -> None:
        """Initialize agents managed by this orchestrator, if not already injected."""
        # This method is primarily for internal setup or when agents are not
        # fully injected at __init__. In current DI approach, it might be less needed.
        logger.debug("Ensuring agents are initialized within orchestrator.")
        # Example: self.agent_router = self.agent_router or AgentRouter()


# Export for direct import will be handled elsewhere to avoid circular imports
