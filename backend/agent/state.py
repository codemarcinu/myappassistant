from typing import List, Any, Optional

class ConversationState:
    """Przechowuje stan bieżącej konwersacji."""
    def __init__(self):
        self.is_awaiting_clarification: bool = False
        self.original_intent: Optional[str] = None
        self.original_entities: Optional[dict] = None
        self.ambiguous_options: List[Any] = []

    def set_clarification_mode(self, intent: str, entities: dict, options: List[Any]):
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options
        print("--- AGENT: Zapisuję stan i przechodzę w tryb oczekiwania na doprecyzowanie. ---")

    def reset(self):
        self.is_awaiting_clarification = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []
        print("--- AGENT: Stan konwersacji zresetowany. ---") 