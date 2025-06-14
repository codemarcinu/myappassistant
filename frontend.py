import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from typing import Union, List, Dict, Any, TypedDict

# Upewnij się, że ścieżka do backendu jest poprawna
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.agents.orchestrator import orchestrator
from backend.agents.state import ConversationState

class Message(TypedDict):
    role: str
    content: Union[str, pd.DataFrame]

# Konfiguracja strony i tytuł
st.set_page_config(page_title="FoodSave AI", layout="wide")
st.title("🤖 FoodSave AI - Twój Asystent Zakupowy")

# Inicjalizacja Pamięci Sesji (Session State)
if "messages" not in st.session_state:
    st.session_state.messages: List[Message] = [
        {"role": "assistant", "content": "Cześć! Jestem Twoim asystentem do spraw wydatków. Jak mogę Ci pomóc?"}
    ]
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = ConversationState()

# --- NOWA, INTELIGENTNA PĘTLA WYŚWIETLAJĄCA HISTORIĘ ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, pd.DataFrame):
            # Jeśli to DataFrame, rysujemy tabelę i wykres
            st.markdown("Przygotowałem dla Ciebie podsumowanie:")
            st.dataframe(content)
            # Sprawdzamy, czy mamy odpowiednie kolumny do narysowania wykresu
            if 'Grupa' in content.columns and 'Wartość' in content.columns:
                st.bar_chart(content.set_index('Grupa'))
        else:
            # Jeśli to zwykły tekst, wyświetlamy go
            st.markdown(str(content))

# Sekcja "Szybkie Akcje"
st.write("---")
st.subheader("Szybkie Akcje")
cols = st.columns(3)
quick_actions = {
    "Pokaż wszystkie paragony": "pokaż wszystkie zakupy",
    "Wydatki wg kategorii": "pokaż podsumowanie wydatków według kategorii",
    "Wydatki wg sklepów": "pokaż wydatki w podziale na sklepy"
}

# Definiujemy funkcję, która będzie obsługiwać kliknięcie przycisku
def handle_action(command: str) -> None:
    st.session_state.action_command = command

for i, (btn_label, command) in enumerate(quick_actions.items()):
    cols[i].button(btn_label, on_click=handle_action, args=(command,), use_container_width=True)

# Pobieramy polecenie z przycisku lub z pola tekstowego
prompt = st.chat_input("Wpisz swoje polecenie...")
if "action_command" in st.session_state and st.session_state.action_command:
    prompt = st.session_state.action_command
    st.session_state.action_command = None

# Główna Pętla Interakcji
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Wywołujemy logikę agenta
    agent_response = asyncio.run(
        orchestrator.process_command(prompt, st.session_state.conversation_state)
    )
    
    # --- NOWA LOGIKA ZAPISU DO HISTORII ---
    response_content: Union[str, pd.DataFrame]
    if isinstance(agent_response, list) and agent_response:
        # Jeśli agent zwrócił dane, tworzymy z nich DataFrame
        df = pd.DataFrame(agent_response)
        if len(df.columns) == 2:
            df.columns = ['Wartość', 'Grupa']
        # Zapisujemy do historii DataFrame, a nie listę!
        response_content = df
    else:
        response_content = str(agent_response)
    
    st.session_state.messages.append({"role": "assistant", "content": response_content})
    st.rerun() 