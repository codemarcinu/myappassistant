# Skopiuj i wklej ten kod jako całą zawartość pliku state.py

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationState:
    """Represents the state of a conversation."""

    session_id: str
    history: List[Dict[str, Any]] = field(default_factory=list)
    is_awaiting_clarification: bool = False
    is_cooking_confirmation: bool = False
    original_intent: Optional[str] = None
    original_entities: Optional[Dict[str, Any]] = None
    ambiguous_options: List[Any] = field(default_factory=list)
    cooking_ingredients: List[Dict[str, Any]] = field(default_factory=list)

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def set_clarification_mode(
        self, intent: str, entities: Dict[str, Any], options: List[Any]
    ):
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options

    def set_cooking_state(self, ingredients: List[Dict[str, Any]]):
        """Set state for cooking confirmation flow."""
        self.is_cooking_confirmation = True
        self.cooking_ingredients = ingredients

    def reset(self):
        self.is_awaiting_clarification = False
        self.is_cooking_confirmation = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []
        self.cooking_ingredients = []

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "session_id": self.session_id,
            "history_length": len(self.history),
            "is_awaiting_clarification": self.is_awaiting_clarification,
            "is_cooking_confirmation": self.is_cooking_confirmation,
            "cooking_ingredients": self.cooking_ingredients,
            "original_intent": self.original_intent,
            "ambiguous_options": self.ambiguous_options,
        }
        return result


# In-memory storage for demonstration purposes.
# In a real application, this would be replaced with Redis, a database, etc.
_agent_states: Dict[str, ConversationState] = {}


def get_agent_state(agent_id: str) -> ConversationState:
    """
    Retrieve the agent state from storage for a given agent_id.
    If no state exists, a new one is created.
    """
    if agent_id not in _agent_states:
        _agent_states[agent_id] = ConversationState(session_id=agent_id)
    return _agent_states[agent_id]


def save_agent_state(agent_id: str, state: ConversationState) -> None:
    """Save the updated agent state to storage."""
    _agent_states[agent_id] = state


def append_to_history(agent_id: str, message: Dict[str, Any]) -> ConversationState:
    """Append a new message to the conversation history and save the state."""
    state = get_agent_state(agent_id)
    state.history.append(message)
    save_agent_state(agent_id, state)
    return state
