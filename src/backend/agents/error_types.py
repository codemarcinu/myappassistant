from typing import Any, AsyncGenerator, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from backend.agents.interfaces import ErrorSeverity


class AgentResponseEnhanced(BaseModel):
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
    model_config = ConfigDict(arbitrary_types_allowed=True)


class AlertConfig(BaseModel):
    """Configuration for alert notifications"""

    enabled: bool = True
    email_alerts: bool = False
    email_recipients: List[str] = []
    slack_alerts: bool = False
    slack_webhook: Optional[str] = None
    min_severity: ErrorSeverity = ErrorSeverity.HIGH
    throttle_period: int = 3600  # seconds between similar alerts


class AgentError(Exception):
    """Base class for agent errors"""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> None:
        self.message = message
        self.severity = severity
        super().__init__(message)


class OrchestratorError(AgentError):
    """Error specific to orchestrator operations"""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.HIGH
    ) -> None:
        super().__init__(message, severity)


class AgentProcessingError(AgentError):
    """Error during agent processing"""

    def __init__(
        self,
        message: str,
        agent_type: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    ) -> None:
        self.agent_type = agent_type
        super().__init__(message, severity)


class AgentInitializationError(AgentError):
    """Error during agent initialization"""

    def __init__(
        self,
        message: str,
        agent_type: str,
        severity: ErrorSeverity = ErrorSeverity.HIGH,
    ) -> None:
        self.agent_type = agent_type
        super().__init__(message, severity)
