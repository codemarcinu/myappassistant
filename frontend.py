import streamlit as st
import asyncio
import sys
import os
import pandas as pd

# Upewnij się, że ścieżka do backendu jest poprawna
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.agents.orchestrator import orchestrator
from backend.agents.state import ConversationState

# Konfiguracja strony i tytuł
st.set_page_config(page_title="FoodSave AI", layout="wide")
st.title("🤖 FoodSave AI - Twój Asystent Zakupowy")

# Inicjalizacja Pamięci Sesji (Session State)
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Cześć! Jestem Twoim asystentem do spraw wydatków. Jak mogę Ci pomóc?"}
    ]
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = ConversationState()

# Wyświetlanie Historii Czatu
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # Sprawdzamy, czy treść wiadomości to DataFrame do wyświetlenia
        if isinstance(message["content"], pd.DataFrame):
            st.dataframe(message["content"])
        else:
            st.markdown(message["content"])

# --- NOWA SEKCJA: SZYBKIE AKCJE ---
st.write("---") # Linia oddzielająca
st.subheader("Szybkie Akcje")
col1, col2, col3 = st.columns(3)

# Definiujemy funkcję, która będzie obsługiwać kliknięcie przycisku
def handle_action(command: str):
    # Ustawiamy polecenie w sesji, aby główna pętla mogła je przetworzyć
    st.session_state.action_command = command

with col1:
    st.button("Pokaż wszystkie paragony", on_click=handle_action, args=("pokaż wszystkie zakupy",), use_container_width=True)

with col2:
    st.button("Wydatki wg kategorii", on_click=handle_action, args=("pokaż podsumowanie wydatków według kategorii",), use_container_width=True)

with col3:
    st.button("Wydatki wg sklepów", on_click=handle_action, args=("pokaż wydatki w podziale na sklepy",), use_container_width=True)
# --- KONIEC NOWEJ SEKCJI ---

# Sprawdzamy, czy kliknięto przycisk, czy wpisano tekst
prompt = st.chat_input("Wpisz swoje polecenie...")
if "action_command" in st.session_state and st.session_state.action_command:
    prompt = st.session_state.action_command
    st.session_state.action_command = None # Czyścimy akcję po jej pobraniu

# Główna Pętla Interakcji
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Agent analizuje..."):
            agent_response = asyncio.run(
                orchestrator.process_command(prompt, st.session_state.conversation_state)
            )
        
        response_for_history = agent_response
        
        if isinstance(agent_response, list) and agent_response:
            response_df = pd.DataFrame(agent_response)
            if len(response_df.columns) == 2:
                response_df.columns = ['Wartość', 'Grupa']
                st.success("Przygotowałem dla Ciebie podsumowanie:")
                st.dataframe(response_df)
                st.bar_chart(response_df.set_index('Grupa'))
                response_for_history = response_df # Zapisujemy DataFrame do historii
            else:
                st.write("Oto dane, które znalazłem:")
                st.dataframe(response_df)
                response_for_history = response_df

        elif isinstance(agent_response, str):
            # Logika kolorowania odpowiedzi
            if "Gotowe" in agent_response or "Pomyślnie" in agent_response:
                st.success(agent_response)
            elif "Niestety" in agent_response or "Błąd" in agent_response:
                st.error(agent_response)
            elif "pytanie" in agent_response.lower() or "wybierz jedną" in agent_response.lower():
                st.info(agent_response)
            else:
                st.markdown(agent_response)
        
    # Convert response to string if it's not already a string
    content_for_history = str(response_for_history) if not isinstance(response_for_history, str) else response_for_history
    st.session_state.messages.append({"role": "assistant", "content": content_for_history})
    # Wymuszamy odświeżenie strony, aby poprawnie wyświetlić nowe wiadomości
    st.rerun() 