import asyncio
import logging
import time
import traceback
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import BaseModel, ValidationError

from ..core.hybrid_llm_client import ModelComplexity, hybrid_llm_client
from ..core.llm_client import llm_client

T = TypeVar("T", bound=BaseModel)
logger = logging.getLogger(__name__)


class ErrorSeverity(str, Enum):
    """Severity levels for agent errors"""

    LOW = "low"  # Non-critical errors, can be handled silently
    MEDIUM = "medium"  # User-visible errors that don't require developer attention
    HIGH = "high"  # Serious errors that should be logged for review
    CRITICAL = "critical"  # Urgent errors requiring immediate attention


class EnhancedAgentResponse(BaseModel):
    """Enhanced agent response with additional context and error handling"""

    success: bool
    data: Optional[Dict[str, Any]] = None
    text: Optional[str] = None
    text_stream: Optional[AsyncGenerator[str, None]] = None
    message: Optional[str] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    error_severity: Optional[ErrorSeverity] = None
    processed_with_fallback: bool = False
    processing_time: float = 0.0
    metadata: Dict[str, Any] = {}

    class Config:
        arbitrary_types_allowed = True


class AlertConfig(BaseModel):
    """Configuration for alert notifications"""

    enabled: bool = True
    email_alerts: bool = False
    email_recipients: List[str] = []
    slack_alerts: bool = False
    slack_webhook: Optional[str] = None
    min_severity: ErrorSeverity = ErrorSeverity.HIGH
    throttle_period: int = 3600  # seconds between similar alerts


class ImprovedBaseAgent(ABC, Generic[T]):
    """
    Enhanced base agent with improved error handling, fallbacks, and alerting.
    This extends the functionality of EnhancedBaseAgent with more robust error
    handling and recovery mechanisms.
    """

    def __init__(self, name: str):
        self.name = name
        self.input_model: Optional[type[T]] = None
        self.alert_config = AlertConfig()
        self.last_alerts: Dict[str, datetime] = {}
        self.fallback_attempts = 0
        self.max_fallback_attempts = 3

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> EnhancedAgentResponse:
        """Main processing method to be implemented by each agent"""
        pass

    def _validate_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against model"""
        if self.input_model:
            try:
                validated = self.input_model.parse_obj(data)
                return validated.dict()
            except ValidationError as ve:
                error_details = {
                    "error_type": "validation_error",
                    "errors": ve.errors(),
                }
                raise ValueError(f"Invalid input data for {self.name}: {ve}") from ve
        return data

    async def execute_with_fallback(
        self,
        func: callable,
        *args,
        fallback_handler: Optional[callable] = None,
        error_severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        **kwargs,
    ) -> Any:
        """
        Execute a function with automatic fallback and error handling

        Args:
            func: The function to execute
            *args: Arguments for the function
            fallback_handler: Optional custom fallback handler
            error_severity: Severity level for errors
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function or fallback
        """
        start_time = time.time()

        try:
            result = await func(*args, **kwargs)
            return result, False, None, time.time() - start_time

        except Exception as e:
            error_info = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat(),
            }
            logger.error(f"Error in {self.name}.{func.__name__}: {str(e)}")

            # Alert if necessary
            if self._should_alert(str(e), error_severity):
                await self._send_alert(
                    f"Error in {self.name}.{func.__name__}", error_info, error_severity
                )

            # Try fallback if provided
            if fallback_handler:
                try:
                    logger.info(f"Attempting fallback for {func.__name__}")
                    result = await fallback_handler(*args, error=e, **kwargs)
                    return result, True, str(e), time.time() - start_time
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
                    error_info["fallback_error"] = str(fallback_error)

            return None, True, str(e), time.time() - start_time

    async def safe_process(self, input_data: Dict[str, Any]) -> EnhancedAgentResponse:
        """
        Process input with comprehensive error handling and fallbacks

        This wraps the process method with additional safety and recovery mechanisms,
        including multi-tiered fallback approaches for different error scenarios.
        """
        start_time = time.time()
        self.fallback_attempts = 0

        try:
            # First try normal processing
            response = await self.process(input_data)
            response.processing_time = time.time() - start_time
            return response

        except Exception as e:
            logger.error(f"Error in {self.name}.process: {str(e)}")

            # Begin fallback sequence
            return await self._multi_tiered_fallback(input_data, e, start_time)

    async def _multi_tiered_fallback(
        self, input_data: Dict[str, Any], original_error: Exception, start_time: float
    ) -> EnhancedAgentResponse:
        """
        Implement multi-tiered fallback strategy for error recovery

        The tiers are:
        1. Prompt rewriting: Try to improve the prompt to avoid the error
        2. Simplified model: Use a simpler model with reduced complexity
        3. Minimal response: Return a basic response acknowledging the issue
        """
        error_info = {
            "agent": self.name,
            "error_type": type(original_error).__name__,
            "message": str(original_error),
            "traceback": traceback.format_exc(),
        }

        # TIER 1: Prompt Rewriting
        rewritten_response = await self._try_prompt_rewriting(
            input_data, original_error
        )
        if rewritten_response and rewritten_response.success:
            rewritten_response.processing_time = time.time() - start_time
            rewritten_response.processed_with_fallback = True
            rewritten_response.metadata["fallback_tier"] = "prompt_rewriting"
            return rewritten_response

        # TIER 2: Simplified Model
        if self.fallback_attempts < self.max_fallback_attempts:
            simplified_response = await self._try_simplified_model(
                input_data, original_error
            )
            if simplified_response and simplified_response.success:
                simplified_response.processing_time = time.time() - start_time
                simplified_response.processed_with_fallback = True
                simplified_response.metadata["fallback_tier"] = "simplified_model"
                return simplified_response

        # TIER 3: Minimal Response
        # If all else fails, return an error response
        total_time = time.time() - start_time

        # Alert developers if this is a critical error
        if self._should_alert(str(original_error), ErrorSeverity.HIGH):
            await self._send_alert(
                f"Critical error in {self.name}", error_info, ErrorSeverity.HIGH
            )

        return EnhancedAgentResponse(
            success=False,
            error=f"Przepraszam, nie mogłem przetworzyć Twojego zapytania: {str(original_error)}",
            error_details=error_info,
            error_severity=ErrorSeverity.MEDIUM,
            processed_with_fallback=True,
            message="Wystąpił problem podczas przetwarzania zapytania. Proszę spróbować inaczej sformułować pytanie.",
            processing_time=total_time,
            metadata={"fallback_tier": "minimal_response"},
        )

    async def _try_prompt_rewriting(
        self, input_data: Dict[str, Any], original_error: Exception
    ) -> Optional[EnhancedAgentResponse]:
        """
        Attempt to rewrite the prompt to avoid the error
        """
        self.fallback_attempts += 1
        logger.info(f"Trying prompt rewriting (attempt {self.fallback_attempts})")

        try:
            # Extract query from input data
            query = input_data.get("query", "")
            if not query:
                # Try other common fields
                for field in ["prompt", "text", "content", "message"]:
                    if field in input_data and isinstance(input_data[field], str):
                        query = input_data[field]
                        break

            if not query or len(query) < 3:
                return None

            # Create rewriting prompt
            rewrite_prompt = (
                f"Poniższe zapytanie spowodowało błąd: '{str(original_error)}'. "
                f"Przepisz zapytanie, aby było jaśniejsze i łatwiejsze do przetworzenia. "
                f"Zachowaj intencję, ale uprość język i strukturę.\n\n"
                f"Oryginalne zapytanie: '{query}'\n\n"
                f"Przepisane zapytanie:"
            )

            # Get rewritten query
            response = await hybrid_llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem przepisującym zapytania.",
                    },
                    {"role": "user", "content": rewrite_prompt},
                ],
                model="gemma2:2b",  # Use simple model for rewriting
                force_complexity=ModelComplexity.SIMPLE,
            )

            if response and "message" in response:
                rewritten_query = response["message"]["content"].strip()
                logger.info(f"Rewritten query: {rewritten_query}")

                # Create new input data with rewritten query
                new_input = input_data.copy()

                # Replace the query in the correct field
                if "query" in new_input:
                    new_input["query"] = rewritten_query
                elif "prompt" in new_input:
                    new_input["prompt"] = rewritten_query
                elif "text" in new_input:
                    new_input["text"] = rewritten_query
                elif "content" in new_input:
                    new_input["content"] = rewritten_query
                elif "message" in new_input:
                    new_input["message"] = rewritten_query

                # Try processing with rewritten query
                response = await self.process(new_input)
                if response.success:
                    response.metadata["original_query"] = query
                    response.metadata["rewritten_query"] = rewritten_query
                    return response

        except Exception as e:
            logger.error(f"Error in prompt rewriting: {str(e)}")

        return None

    async def _try_simplified_model(
        self, input_data: Dict[str, Any], original_error: Exception
    ) -> Optional[EnhancedAgentResponse]:
        """
        Attempt to process with a simplified model
        """
        self.fallback_attempts += 1
        logger.info(f"Trying simplified model (attempt {self.fallback_attempts})")

        try:
            # Extract query for simplification
            query = input_data.get("query", "")
            if not query:
                # Try other common fields
                for field in ["prompt", "text", "content", "message"]:
                    if field in input_data and isinstance(input_data[field], str):
                        query = input_data[field]
                        break

            if not query:
                return None

            # Create simplification prompt
            simplify_prompt = (
                f"Zapytanie użytkownika: '{query}'\n\n"
                f"Udziel prostej, zwięzłej odpowiedzi na to zapytanie. "
                f"Jeśli zapytanie jest zbyt złożone lub niejasne, poproś o doprecyzowanie."
            )

            # Use smaller model with simpler approach
            response = await hybrid_llm_client.chat(
                messages=[
                    {
                        "role": "system",
                        "content": "Jesteś pomocnym asystentem udzielającym prostych odpowiedzi.",
                    },
                    {"role": "user", "content": simplify_prompt},
                ],
                model="llama3:8b",  # Use mid-size model
                force_complexity=ModelComplexity.STANDARD,
            )

            if response and "message" in response:
                simplified_answer = response["message"]["content"].strip()

                # Create successful response
                return EnhancedAgentResponse(
                    success=True,
                    text=simplified_answer,
                    message="Odpowiedź wygenerowana w trybie uproszczonym",
                    metadata={"simplified": True, "original_query": query},
                )

        except Exception as e:
            logger.error(f"Error in simplified model approach: {str(e)}")

        return None

    def _should_alert(self, error_message: str, severity: ErrorSeverity) -> bool:
        """
        Determine if an alert should be sent based on severity and throttling
        """
        if not self.alert_config.enabled:
            return False

        # Check severity threshold
        severity_levels = {
            ErrorSeverity.LOW: 1,
            ErrorSeverity.MEDIUM: 2,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.CRITICAL: 4,
        }

        if severity_levels[severity] < severity_levels[self.alert_config.min_severity]:
            return False

        # Check throttling
        error_key = f"{self.name}:{error_message[:50]}"
        now = datetime.now()

        if error_key in self.last_alerts:
            time_since_last = (now - self.last_alerts[error_key]).total_seconds()
            if time_since_last < self.alert_config.throttle_period:
                return False

        # Update last alert time
        self.last_alerts[error_key] = now
        return True

    async def _send_alert(
        self, subject: str, error_info: Dict[str, Any], severity: ErrorSeverity
    ) -> None:
        """
        Send alert notification via configured channels
        """
        if not self.alert_config.enabled:
            return

        alert_text = (
            f"ALERT: {subject}\n"
            f"Severity: {severity}\n"
            f"Agent: {self.name}\n"
            f"Time: {datetime.now().isoformat()}\n\n"
            f"Error: {error_info.get('error', 'Unknown error')}\n"
            f"Traceback: {error_info.get('traceback', 'No traceback')}"
        )

        logger.warning(f"AGENT ALERT: {subject} ({severity})")

        # In a real implementation, this would send emails/Slack messages
        # For now, we'll just log it
        if self.alert_config.email_alerts and self.alert_config.email_recipients:
            logger.info(
                f"Would send email alert to {self.alert_config.email_recipients}"
            )

        if self.alert_config.slack_alerts and self.alert_config.slack_webhook:
            logger.info(f"Would send Slack alert to webhook")

    async def _stream_llm_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        retries: int = 3,
        backoff_factor: float = 0.5,
    ) -> AsyncGenerator[str, None]:
        """Stream LLM response with retries"""
        attempt = 0

        while attempt < retries:
            try:
                async for chunk in hybrid_llm_client.chat(
                    messages=messages, model=model, stream=True
                ):
                    if "message" in chunk and "content" in chunk["message"]:
                        yield chunk["message"]["content"]
                return
            except Exception as e:
                logger.debug(f"LLM streaming error: {str(e)}")
                attempt += 1
                if attempt < retries:
                    wait_time = backoff_factor * (2 ** (attempt - 1))
                    logger.warning(
                        f"LLM streaming attempt {attempt} failed, retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)

        logger.error(f"LLM streaming failed after {retries} attempts")
        yield f"Error: Failed to generate response after {retries} attempts"


# Use ImprovedBaseAgent in place of EnhancedBaseAgent for improved error handling
EnhancedBaseAgentWithFallback = ImprovedBaseAgent
