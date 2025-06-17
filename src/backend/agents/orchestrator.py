"""
Kompatybilność z poprzednią wersją API.
Ten moduł importuje elementy z enhanced_orchestrator,
zapewniając kompatybilność ze starszym kodem.
"""

from enum import Enum
import importlib
import sys


class IntentType(Enum):
    WEATHER = "Zapytanie o pogodę lub warunki atmosferyczne"
    SEARCH = "Ogólne wyszukiwanie informacji"
    RAG = "Zapytanie o wiedzę zgromadzoną w dokumentach"
    COOKING = "Zapytanie związane z gotowaniem, przepisami lub planowaniem posiłków"
    SHOPPING = "Zapytanie związane z zakupami lub zarządzaniem produktami"
    CHAT = "Konwersacja ogólna lub small talk"
    UNKNOWN = "Intencja nie pasuje do żadnej z powyższych kategorii"


# Klasa proxy do opóźnionego tworzenia Orchestratora
class Orchestrator:
    def __new__(cls, *args, **kwargs):
        # Importujemy klasę dynamicznie, aby uniknąć cyklicznych zależności
        # Używamy importlib zamiast bezpośredniego importu
        module_path = 'backend.agents.enhanced_orchestrator'
        
        # Sprawdź, czy moduł jest już w cache - jeśli tak, usuń go, aby uniknąć częściowo zainicjalizowanego modułu
        if module_path in sys.modules:
            del sys.modules[module_path]
            
        # Dynamicznie importuj moduł
        module = importlib.import_module(module_path)
        
        # Pobierz klasę EnhancedOrchestrator z modułu
        EnhancedOrchestrator = getattr(module, 'EnhancedOrchestrator')
        
        # Utwórz i zwróć instancję
        return EnhancedOrchestrator(*args, **kwargs)