from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class Message:
    """Reprezentuje pojedynczą wiadomość w konwersacji."""

    role: str  # 'user' lub 'assistant'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


class ConversationState:
    """
    Klasa zarządzająca stanem konwersacji.
    Przechowuje informacje o tym, czy system oczekuje na doprecyzowanie
    i jakie dane są potrzebne do kontynuacji.
    """

    def __init__(self, max_history: int = 5):
        self.max_history = max_history
        self.reset()

    def reset(self):
        """
        Resetuje stan konwersacji do wartości początkowych.
        """
        self.is_awaiting_clarification = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []
        # Używamy deque zamiast listy dla lepszej wydajności
        self.conversation_history: deque[Message] = deque(maxlen=self.max_history)

    def set_clarification_mode(self, intent: str, entities: Dict, options: List[Any]):
        """
        Ustawia stan oczekiwania na doprecyzowanie wyboru.
        """
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options

    def add_message(self, role: str, content: str):
        """
        Dodaje nową wiadomość do historii konwersacji.
        Automatycznie usuwa najstarsze wiadomości, jeśli przekroczymy limit.
        """
        self.conversation_history.append(Message(role=role, content=content))

    def get_conversation_context(self) -> str:
        """
        Zwraca sformatowany kontekst konwersacji do użycia w promptach.
        """
        if not self.conversation_history:
            return ""

        context = "Historia konwersacji:\n"
        for msg in self.conversation_history:
            context += f"{msg.role.upper()}: {msg.content}\n"
        return context

    def to_dict(self) -> Dict[str, Any]:
        """
        Konwertuje stan konwersacji do słownika do serializacji.
        """
        return {
            "is_awaiting_clarification": self.is_awaiting_clarification,
            "original_intent": self.original_intent,
            "original_entities": self.original_entities,
            "ambiguous_options": self.ambiguous_options,
            "conversation_history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in self.conversation_history
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationState":
        """
        Tworzy instancję ConversationState z danych serializowanych.
        """
        state = cls()
        state.is_awaiting_clarification = data.get("is_awaiting_clarification", False)
        state.original_intent = data.get("original_intent")
        state.original_entities = data.get("original_entities")
        state.ambiguous_options = data.get("ambiguous_options", [])

        # Przywracanie historii konwersacji
        for msg_data in data.get("conversation_history", []):
            state.conversation_history.append(
                Message(
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=datetime.fromisoformat(msg_data["timestamp"]),
                )
            )

        return state
