import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from typing import Union, List, Dict, Any, TypedDict
import matplotlib.pyplot as plt
from backend.agents.base_agent import BaseAgent
from backend.agents.orchestrator import orchestrator

# Upewnij się, że ścieżka do backendu jest poprawna
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

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
    
    # Debugowanie - wyświetlamy surowe dane
    st.write("Debug - Typ odpowiedzi:", type(agent_response))
    st.write("Debug - Zawartość odpowiedzi:", agent_response)
    
    # Inicjalizujemy zmienną response_for_history
    response_for_history = None

    if isinstance(agent_response, list) and agent_response:
        response_text_for_history = "Przygotowałem dla Ciebie podsumowanie."
        st.success(response_text_for_history)
        
        try:
            # Dynamiczne tworzenie DataFrame i nadawanie nazw kolumnom
            df = pd.DataFrame(agent_response)
            st.write("Debug - DataFrame przed przetworzeniem:", df)
            
            if len(df.columns) == 2:
                # Zakładamy, że pierwsza kolumna to wartość, druga to etykieta
                df.columns = ['Wartość', 'Grupa']
                df = df.set_index('Grupa') # Ustawiamy grupę jako indeks
                st.write("Debug - DataFrame po przetworzeniu:", df)
            
            st.write("### Podsumowanie w Tabeli")
            st.dataframe(df)
            
            # Używamy kolumn do stworzenia dwóch layoutów
            col1, col2 = st.columns(2)

            with col1:
                st.write("### Wydatki na Wykresie Słupkowym")
                st.bar_chart(df)

            with col2:
                st.write("### Struktura Wydatków (Wykres Kołowy)")
                # Tworzymy wykres kołowy za pomocą Matplotlib
                fig, ax = plt.subplots()
                ax.pie(df['Wartość'], labels=df.index.tolist(), autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Zapewnia, że wykres jest idealnym kołem
                
                # Wyświetlamy wykres w Streamlit
                st.pyplot(fig)

            # Zapisujemy do historii DataFrame
            response_for_history = df

        except Exception as e:
            st.error(f"Wystąpił błąd podczas tworzenia wykresu: {e}")
            st.write("Debug - Szczegóły błędu:", str(e))
            response_for_history = str(e)

    elif isinstance(agent_response, str):
        response_text_for_history = agent_response
        st.success(response_text_for_history)
        response_for_history = agent_response

    # Konwertujemy DataFrame na string dla historii
    if isinstance(response_for_history, pd.DataFrame):
        st.session_state.messages.append({"role": "assistant", "content": response_for_history.to_string()})
    else:
        st.session_state.messages.append({"role": "assistant", "content": str(response_for_history)})
    st.rerun() 