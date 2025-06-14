from typing import Any, Dict, List

class ConversationState:
    """
    Klasa zarządzająca stanem konwersacji.
    Przechowuje informacje o tym, czy system oczekuje na doprecyzowanie
    i jakie dane są potrzebne do kontynuacji.
    """
    def __init__(self):
        self.reset()

    def reset(self):
        """
        Resetuje stan konwersacji do wartości początkowych.
        """
        self.is_awaiting_clarification = False
        self.original_intent = None
        self.original_entities = None
        self.ambiguous_options = []

    def set_clarification_mode(self, intent: str, entities: Dict, options: List[Any]):
        """
        Ustawia stan oczekiwania na doprecyzowanie wyboru.
        """
        self.is_awaiting_clarification = True
        self.original_intent = intent
        self.original_entities = entities
        self.ambiguous_options = options 