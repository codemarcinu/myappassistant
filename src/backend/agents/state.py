from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ConversationState:
    current_intent: Optional[str] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    is_awaiting_clarification: bool = False
    ambiguous_options: Optional[List[Any]] = None
    original_intent: Optional[str] = None
    original_entities: Optional[Dict[str, Any]] = None

    def add_message(self, role: str, content: str, data: Any = None) -> None:
        message = {"role": role, "content": content}
        if data is not None:
            message["data"] = data
        self.history.append(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_intent": self.current_intent,
            "history": self.history,
            "is_awaiting_clarification": self.is_awaiting_clarification,
            "ambiguous_options": self.ambiguous_options,
            "original_intent": self.original_intent,
            "original_entities": self.original_entities,
        }

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> "ConversationState":
        if not data:
            return cls()
        return cls(
            current_intent=data.get("current_intent"),
            history=data.get("history", []),
            is_awaiting_clarification=data.get("is_awaiting_clarification", False),
            ambiguous_options=data.get("ambiguous_options"),
            original_intent=data.get("original_intent"),
            original_entities=data.get("original_entities"),
        )

    def set_clarification_mode(
        self, intent: str, entities: Dict[str, Any], options: List[Any]
    ) -> None:
        self.is_awaiting_clarification = True
        self.ambiguous_options = options
        self.original_intent = intent
        self.original_entities = entities

    def reset(self) -> None:
        self.is_awaiting_clarification = False
        self.ambiguous_options = None
        self.original_intent = None
        self.original_entities = None


def get_agent_state(agent_id: str) -> dict:
    return {}


def save_agent_state(agent_id: str, state: dict) -> None:
    pass
