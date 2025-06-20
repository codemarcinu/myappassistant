import logging
from typing import Any, Dict

from .interfaces import AgentResponse, IResponseGenerator, MemoryContext

logger = logging.getLogger(__name__)


class ResponseGenerator(IResponseGenerator):
    """Implementation of response generation logic"""

    def __init__(self):
        self.response_templates = {
            "success": "Operacja zakończona pomyślnie: {message}",
            "error": "Wystąpił błąd: {error}",
            "fallback": "Używam alternatywnego rozwiązania: {message}",
        }

    async def generate_response(
        self, context: MemoryContext, agent_response: AgentResponse
    ) -> AgentResponse:
        """Generate final response based on context and agent response"""
        try:
            # Update context with the response
            context.last_response = agent_response
            context.last_updated = context.last_updated

            # Add context metadata to response
            if agent_response.metadata is None:
                agent_response.metadata = {}

            agent_response.metadata.update(
                {
                    "session_id": context.session_id,
                    "context_created": context.created_at.isoformat(),
                    "context_updated": context.last_updated.isoformat(),
                    "active_agents_count": len(context.active_agents),
                }
            )

            # Format response based on success/error status
            if agent_response.success:
                if agent_response.text:
                    agent_response.text = self.response_templates["success"].format(
                        message=agent_response.text
                    )
            else:
                if agent_response.error:
                    agent_response.text = self.response_templates["error"].format(
                        error=agent_response.error
                    )

            logger.debug(f"Generated response for session {context.session_id}")
            return agent_response

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return AgentResponse(
                success=False,
                error=f"Błąd generowania odpowiedzi: {str(e)}",
                severity="ERROR",
            )

    async def generate_error_response(
        self, error: Exception, context: Dict[str, Any]
    ) -> AgentResponse:
        """Generate user-friendly error response"""
        error_message = str(error) if error else "Nieznany błąd"

        return AgentResponse(
            success=False,
            error=error_message,
            severity="ERROR",
            text=self.response_templates["error"].format(error=error_message),
            metadata={"error_type": type(error).__name__, "context": context},
        )

    async def generate_fallback_response(
        self, context: Dict[str, Any], message: str
    ) -> AgentResponse:
        """Generate fallback response when primary agent fails"""
        return AgentResponse(
            success=True,
            text=self.response_templates["fallback"].format(message=message),
            severity="WARNING",
            fallback_used=True,
            metadata={"fallback_reason": "primary_agent_failed", "context": context},
        )
