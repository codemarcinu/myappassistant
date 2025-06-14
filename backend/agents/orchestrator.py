# PRAWIDŁOWA ZAWARTOŚĆ DLA PLIKU orchestrator.py

import json
import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from ..core.llm_client import ollama_client
from ..config import settings
from .prompts import get_intent_recognition_prompt, get_entity_extraction_prompt, get_resolver_prompt
from .utils import extract_json_from_text
from .state import ConversationState
from . import tools

class IntentType(Enum):
    """
    Typy intencji, które system może rozpoznać.
    """
    ADD_PURCHASE = "DODAJ_ZAKUPY"
    READ_SUMMARY = "CZYTAJ_PODSUMOWANIE"
    UPDATE_ITEM = "UPDATE_ITEM"
    DELETE_ITEM = "DELETE_ITEM"
    UPDATE_PURCHASE = "UPDATE_PURCHASE"
    DELETE_PURCHASE = "DELETE_PURCHASE"
    UNKNOWN = "UNKNOWN"

class AgentOrchestrator:
    """
    Klasa odpowiedzialna za zarządzanie i delegowanie zadań do odpowiednich agentów.
    Teraz pełni rolę głównego "mózgu" systemu.
    """
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Orchestrator zainicjalizowany jako główny mózg systemu")

    async def recognize_intent(self, user_command: str) -> str:
        """
        Analizuje polecenie użytkownika i zwraca rozpoznaną intencję.
        """
        prompt = get_intent_recognition_prompt(user_command)
        messages = [
            {'role': 'system', 'content': "Jesteś precyzyjnym systemem klasyfikacji intencji. Zawsze zwracaj tylko JSON."},
            {'role': 'user', 'content': prompt}
        ]
        response = await ollama_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        try:
            result = extract_json_from_text(response['message']['content'])
            return result.get('intent', 'UNKNOWN')
        except Exception as e:
            self.logger.error(f"Błąd podczas rozpoznawania intencji: {e}")
            return 'UNKNOWN'

    async def extract_entities(self, user_command: str, intent: str) -> Dict:
        """
        Ekstrahuje encje z polecenia użytkownika na podstawie rozpoznanej intencji.
        """
        prompt = get_entity_extraction_prompt(user_command, intent)
        messages = [
            {'role': 'system', 'content': "Jesteś precyzyjnym systemem ekstrakcji encji. Zawsze zwracaj tylko JSON."},
            {'role': 'user', 'content': prompt}
        ]
        response = await ollama_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        try:
            return extract_json_from_text(response['message']['content'])
        except Exception as e:
            self.logger.error(f"Błąd podczas ekstrakcji encji: {e}")
            return {}

    async def resolve_ambiguity(self, options: list, user_reply: str) -> Any | None:
        """
        Rozwiązuje niejednoznaczność w wyborze użytkownika.
        """
        prompt = get_resolver_prompt(options, user_reply)
        messages = [
            {'role': 'system', 'content': "Jesteś precyzyjnym systemem rozwiązywania niejednoznaczności. Zawsze zwracaj tylko JSON."},
            {'role': 'user', 'content': prompt}
        ]
        response = await ollama_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        try:
            result = extract_json_from_text(response['message']['content'])
            choice = result.get('choice')
            if choice and 1 <= choice <= len(options):
                return options[choice - 1]
        except Exception as e:
            self.logger.error(f"Błąd podczas rozwiązywania niejednoznaczności: {e}")
        return None

    async def process_command(self, user_command: str, state: ConversationState) -> str | List[Any]:
        """
        Główna funkcja orkiestratora, zarządzająca całym przepływem.
        WERSJA Z POPRAWIONĄ LOGIKĄ DLA WYNIKÓW ANALITYCZNYCH.
        """
        # Ścieżka 1: Użytkownik doprecyzowuje poprzednie polecenie
        if state.is_awaiting_clarification:
            chosen_object = await self.resolve_ambiguity(state.ambiguous_options, user_command)
            if chosen_object and state.original_intent and state.original_entities:
                success = await tools.execute_database_action(state.original_intent, chosen_object, state.original_entities)
                state.reset()
                return "Gotowe, operacja została wykonana." if success else "Coś poszło nie tak podczas zapisu."
            else:
                state.reset()
                return "Niestety, nie udało mi się zrozumieć wyboru. Zacznijmy od nowa."

        # Ścieżka 2: Nowe polecenie
        intent_str = await self.recognize_intent(user_command)
        try:
            intent = IntentType(intent_str)
        except ValueError:
            intent = IntentType.UNKNOWN
            
        if intent == IntentType.UNKNOWN:
            return "Przepraszam, nie potrafię pomóc w tej kwestii. Skupmy się na wydatkach."
        
        entities = await self.extract_entities(user_command, intent.value)
        
        # Najpierw obsługujemy intencje, które nie wymagają wyszukiwania
        if intent == IntentType.ADD_PURCHASE:
            print(f"DEBUG: Otrzymane encje dla DODAJ_ZAKUPY: {entities}")
            success = await tools.execute_database_action(intent.value, None, entities)
            return "Pomyślnie dodałem nowy paragon." if success else "Wystąpił błąd podczas dodawania paragonu."
        
        # Następnie obsługujemy zapytania analityczne, które zawsze zwracają listę wyników
        if intent == IntentType.READ_SUMMARY:
            return await tools.find_database_object(intent.value, entities)

        # Dla pozostałych intencji (UPDATE, DELETE) uruchamiamy logikę z obsługą niejednoznaczności
        found_objects = await tools.find_database_object(intent.value, entities)
        
        if len(found_objects) == 1:
            success = await tools.execute_database_action(intent.value, found_objects[0], entities)
            return "Gotowe, operacja wykonana." if success else "Coś poszło nie tak podczas zapisu."
            
        elif len(found_objects) > 1:
            state.set_clarification_mode(intent.value, entities, found_objects)
            return tools.generate_clarification_question_text(found_objects)
            
        else: # len == 0
            return "Niestety, nie znalazłem niczego pasującego do Twojego opisu."

# Tworzymy instancję orkiestratora
orchestrator = AgentOrchestrator()