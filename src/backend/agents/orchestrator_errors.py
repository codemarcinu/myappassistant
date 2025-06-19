class OrchestratorError(Exception):
    """Base class for orchestrator errors."""

    pass


class AgentProcessingError(OrchestratorError):
    """Error during agent processing."""

    pass


class ServiceUnavailableError(OrchestratorError):
    """Required service is unavailable."""

    pass


class IntentRecognitionError(OrchestratorError):
    """Error during intent recognition."""

    pass


class MemoryManagerError(OrchestratorError):
    """Error related to memory management."""

    pass


class ProfileManagerError(OrchestratorError):
    """Error related to user profile management."""

    pass
