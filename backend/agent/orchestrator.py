import json
from typing import Dict

from ..core.llm_client import llm_client
from ..config import settings
from ..core.utils import extract_json_from_text

# NOWY, POTĘŻNY PROMPT DLA ORKIESTRATORA
INTENT_RECOGNITION_PROMPT = """Twoim jedynym zadaniem jest precyzyjna analiza polecenia użytkownika i zwrócenie jego głównej intencji w formacie JSON. Zawsze zwracaj tylko i wyłącznie obiekt JSON z jednym kluczem: 'intencja'.

Dostępne intencje to:
- DODAJ_ZAKUPY: Gdy użytkownik chce dodać nowy paragon lub produkty, które kupił.
- CZYTAJ_PODSUMOWANIE: Gdy użytkownik pyta o podsumowanie wydatków.
- UPDATE_ITEM: Gdy użytkownik chce zmienić dane konkretnego produktu na paragonie.
- DELETE_ITEM: Gdy użytkownik chce usunąć konkretny produkt z paragonu.
- UPDATE_PURCHASE: Gdy użytkownik chce zmienić ogólne dane paragonu (sklep, data).
- DELETE_PURCHASE: Gdy użytkownik chce usunąć cały paragon.
- UNKNOWN: Gdy polecenie jest niejasne lub nie pasuje do żadnej intencji.

### Przykłady ###

---
Użytkownik: "dodaj paragon z żabki, kupiłem wodę i colę"
Ty: {"intencja": "DODAJ_ZAKUPY"}
---
Użytkownik: "wczoraj byłem w Biedronce i kupiłem 2 chleby i masło"
Ty: {"intencja": "DODAJ_ZAKUPY"}
---
Użytkownik: "ile wydałem w tym tygodniu?"
Ty: {"intencja": "CZYTAJ_PODSUMOWANIE"}
---
Użytkownik: "zmień cenę chleba z wczoraj na 5.50"
Ty: {"intencja": "UPDATE_ITEM"}
---
Użytkownik: "usuń paragon z lidla z 10 czerwca"
Ty: {"intencja": "DELETE_PURCHASE"}
---
Użytkownik: "opowiedz mi dowcip"
Ty: {"intencja": "UNKNOWN"}
---
"""

async def recognize_intent(user_command: str) -> str:
    """
    Używa LLM do rozpoznania intencji użytkownika z użyciem zaawansowanego promptu.
    """
    print(f"ORCHESTRATOR: Rozpoznaję intencję dla '{user_command}'...")
    
    messages = [
        {'role': 'system', 'content': INTENT_RECOGNITION_PROMPT},
        {'role': 'user', 'content': user_command}
    ]
    
    try:
        response = await llm_client.chat(
            model=settings.DEFAULT_CHAT_MODEL,
            messages=messages,
            stream=False,
            options={'temperature': 0.0}
        )
        raw_response = response['message']['content']
        json_string = extract_json_from_text(raw_response)
        
        if not json_string:
            return "UNKNOWN"
            
        return json.loads(json_string).get("intencja", "UNKNOWN")
    except Exception as e:
        print(f"Błąd w Orkiestratorze: {e}")
        return "UNKNOWN" 