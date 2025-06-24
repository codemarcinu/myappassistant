from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import (Any, AsyncGenerator, Dict, List, Optional, Type, TypeVar,
                    Union)

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class BaseAgent(ABC):
    """Abstract base class for all agents"""

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> "AgentResponse":
        """Process input data and return results"""

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return agent metadata including capabilities"""

    @abstractmethod
    def get_dependencies(self) -> List[Type["BaseAgent"]]:
        """List of agent types this agent depends on"""

    @abstractmethod
    def is_healthy(self) -> bool:
        """Check if agent is functioning properly"""


# Alias for backward compatibility
IBaseAgent = BaseAgent


class AgentResponse(BaseModel):
    """Enhanced response model with additional metadata and streaming support"""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    text: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    severity: Optional[str] = None
    message: Optional[str] = None
    text_stream: Optional[AsyncGenerator[str, None]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[float] = None
    processing_time: Optional[float] = None
    model_used: Optional[str] = None
    confidence: Optional[float] = None
    fallback_used: Optional[bool] = None
    retries: Optional[int] = None
    warnings: Optional[List[str]] = None
    raw_response: Optional[Union[Dict[str, Any], str]] = None
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    encoding: Optional[str] = None
    cost: Optional[float] = None
    tokens_used: Optional[int] = None
    version: str = "1.0.0"
    api_version: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    is_cached: Optional[bool] = None
    cache_key: Optional[str] = None
    cache_ttl: Optional[int] = None


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(Enum):
    """Types of agents available in the system"""

    CHEF = "Chef"
    WEATHER = "Weather"
    SEARCH = "Search"
    RAG = "RAG"
    OCR = "OCR"
    CATEGORIZATION = "Categorization"
    MEAL_PLANNER = "MealPlanner"
    ANALYTICS = "Analytics"
    GENERAL_CONVERSATION = "GeneralConversation"  # Nowy typ dla swobodnych konwersacji
    GENERAL = "General"  # Alias dla GENERAL_CONVERSATION
    COOKING = "Cooking"  # Alias dla CHEF
    CODE = "Code"  # Dla generowania kodu
    SHOPPING = "Shopping"  # Dla zakupów


class AgentStatus(Enum):
    """Possible states of an agent"""

    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    DEGRADED = "degraded"
    IDLE = "idle"


class AgentConfig(BaseModel):
    """Configuration for agent initialization"""

    agent_type: AgentType
    dependencies: List[AgentType]
    settings: Dict[str, Any]
    timeout: int = 30
    retry_count: int = 3
    cache_enabled: bool = True
    fallback_enabled: bool = True


class IntentData:
    """Data structure for intent detection results"""

    def __init__(
        self, type: str, entities: Optional[Dict] = None, confidence: float = 1.0
    ) -> None:
        self.type = type
        self.entities = entities if entities is not None else {}
        self.confidence = confidence


class MemoryContext:
    """Context for maintaining conversation state and memory"""

    def __init__(self, session_id: str, history: Optional[List[Dict]] = None) -> None:
        self.session_id = session_id
        self.history = history if history is not None else []
        self.active_agents: Dict[str, BaseAgent] = {}
        self.last_response: Optional[AgentResponse] = None
        self.created_at: datetime = datetime.now()
        self.last_updated: datetime = datetime.now()


# Interface abstractions
class IAgentRouter(ABC):
    @abstractmethod
    async def route_to_agent(
        self, intent: IntentData, context: MemoryContext, user_command: str = ""
    ) -> AgentResponse:
        """Routes the intent to the appropriate agent and returns its response."""

    @abstractmethod
    def register_agent(self, agent_type: AgentType, agent: BaseAgent) -> None:
        """Register an agent implementation for a specific type"""

    @abstractmethod
    def get_agent(self, agent_type: AgentType) -> BaseAgent:
        """Get registered agent by type"""


class IMemoryManager(ABC):
    @abstractmethod
    async def store_context(self, context: MemoryContext) -> None:
        """Store context for later retrieval"""

    @abstractmethod
    async def retrieve_context(self, session_id: str) -> Optional[MemoryContext]:
        """Retrieve context for session if it exists"""

    @abstractmethod
    async def update_context(
        self, context: MemoryContext, new_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update existing context with optional new data"""

    @abstractmethod
    async def clear_context(self, session_id: str) -> None:
        """Clear context for session"""


class IResponseGenerator(ABC):
    @abstractmethod
    async def generate_response(
        self, context: MemoryContext, agent_response: AgentResponse
    ) -> AgentResponse:
        """Generate final response based on context and agent response"""


class IErrorHandler(ABC):
    @abstractmethod
    async def handle_error(
        self, error: Exception, context: Dict[str, Any]
    ) -> AgentResponse:
        """Handle errors in agent processing"""


class IAlertService(ABC):
    @abstractmethod
    async def send_alert(self, message: str, severity: ErrorSeverity) -> None:
        """Send alert notification"""


class IFallbackProvider(ABC):
    @abstractmethod
    async def get_fallback_response(self, context: Dict[str, Any]) -> AgentResponse:
        """Get fallback response when primary agent fails"""


class AgentPlugin(ABC):
    """Interface for agent plugins"""

    @abstractmethod
    def initialize(self, agent: BaseAgent) -> None:
        pass

    @abstractmethod
    async def pre_process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def post_process(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        pass


# Type aliases for backward compatibility
AgentResponseType = AgentResponse
BaseAgentType = BaseAgent


class IChefAgent(BaseAgent):
    """Interface for Chef agent"""

    @abstractmethod
    async def generate_recipe(self, ingredients: List[str]) -> AgentResponse:
        pass

    @abstractmethod
    async def adjust_recipe(
        self, recipe_id: str, adjustments: Dict[str, Any]
    ) -> AgentResponse:
        pass


class ISearchAgent(BaseAgent):
    """Interface for Search agent"""

    @abstractmethod
    async def search_recipes(self, query: str) -> AgentResponse:
        pass

    @abstractmethod
    async def search_ingredients(self, query: str) -> AgentResponse:
        pass


class IAnalyticsAgent(BaseAgent):
    """Interface for Analytics agent"""

    @abstractmethod
    async def track_usage(self, event_data: Dict[str, Any]) -> AgentResponse:
        pass

    @abstractmethod
    async def generate_report(self, report_type: str) -> AgentResponse:
        pass


# Common data structures and enums
class IntentType(Enum):
    """Types of user intents"""

    GREETING = "greeting"
    COOKING = "cooking"
    SEARCH = "search"
    WEATHER = "weather"
    OCR = "ocr"
    ANALYTICS = "analytics"
    MEAL_PLANNING = "meal_planning"
    CATEGORIZATION = "categorization"
    RAG = "rag"
    GENERAL = "general"
    # Nowe typy dla rozpoznawania kontekstu konwersacji
    SHOPPING_CONVERSATION = (
        "shopping_conversation"  # Rozmowa o zakupach, paragonach, wydatkach
    )
    FOOD_CONVERSATION = "food_conversation"  # Rozmowa o jedzeniu, przepisach, gotowaniu
    GENERAL_CONVERSATION = "general_conversation"  # Swobodna rozmowa na dowolny temat
    INFORMATION_QUERY = "information_query"  # Zapytanie o informacje z internetu


class ProcessingStatus(Enum):
    """Status of agent processing"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CacheStrategy(Enum):
    """Cache strategies for agents"""

    NONE = "none"
    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"


# Common configuration models
class LLMConfig(BaseModel):
    """Configuration for LLM models"""

    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class AgentDependencyConfig(BaseModel):
    """Configuration for agent dependencies"""

    agent_type: AgentType
    required: bool = True
    timeout: int = 30
    retry_count: int = 3


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker"""

    fail_max: int = 5
    reset_timeout: int = 30
    exclude_exceptions: List[str] = []


class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""

    requests_per_minute: int = 60
    burst_size: int = 10
    window_size: int = 60


# Common utility classes
class AgentMetrics:
    """Metrics tracking for agent performance"""

    def __init__(self) -> None:
        self.request_count: int = 0
        self.success_count: int = 0
        self.error_count: int = 0
        self.total_processing_time: float = 0.0
        self.average_response_time: float = 0.0

    def record_request(self, success: bool, processing_time: float) -> None:
        """Record a request and its metrics"""
        self.request_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        self.total_processing_time += processing_time
        self.average_response_time = self.total_processing_time / self.request_count

    def get_success_rate(self) -> float:
        """Calculate success rate as percentage"""
        if self.request_count == 0:
            return 0.0
        return (self.success_count / self.request_count) * 100


class AgentHealthCheck:
    """Health check information for agents"""

    def __init__(self) -> None:
        self.is_healthy: bool = True
        self.last_check: datetime = datetime.now()
        self.error_message: Optional[str] = None
        self.response_time: Optional[float] = None

    def update(
        self,
        is_healthy: bool,
        error_message: Optional[str] = None,
        response_time: Optional[float] = None,
    ) -> None:
        """Update health check status"""
        self.is_healthy = is_healthy
        self.last_check = datetime.now()
        self.error_message = error_message
        self.response_time = response_time

    def is_stale(self, max_age_seconds: int = 300) -> bool:
        """Check if health check is stale"""
        if self.last_check is None:
            return True
        return (datetime.now() - self.last_check).total_seconds() > max_age_seconds
