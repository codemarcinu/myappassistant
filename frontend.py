import streamlit as st
import asyncio
import sys
import os
from backend.agents.orchestrator import orchestrator
from backend.agents.state import ConversationState
import pandas as pd

# Kluczowy krok: dodajemy ścieżkę do katalogu głównego projektu,
# aby Python mógł znaleźć nasze moduły z backendu.
# Upewnij się, że ten skrypt jest w głównym katalogu projektu.
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# --- Konfiguracja strony i tytuł ---
st.set_page_config(page_title="FoodSave AI", page_icon="🛒")
st.title("FoodSave AI - Twój Asystent Zakupowy")

# --- Inicjalizacja Pamięci Sesji (Session State) ---
# To wykona się tylko raz na początku sesji użytkownika.

# Inicjalizujemy historię czatu, jeśli jeszcze nie istnieje
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Cześć! Jestem Twoim asystentem do spraw wydatków. Jak mogę Ci pomóc?"}
    ]

# Inicjalizujemy stan konwersacji agenta dla tej sesji
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = ConversationState()

# --- Wyświetlanie Historii Czatu ---
# Ta pętla rysuje na ekranie wszystkie dotychczasowe wiadomości z pamięci sesji
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- Główna Pętla Interakcji ---
# Czekamy na nowe polecenie od użytkownika w polu na dole ekranu
if prompt := st.chat_input("Wpisz swoje polecenie..."):
    # Dodaj wiadomość użytkownika do historii i ją wyświetl
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Wyświetl animację "myślenia" i wywołaj logikę agenta
    with st.chat_message("assistant"):
        with st.spinner("Agent analizuje..."):
            agent_response = asyncio.run(
                orchestrator.process_command(prompt, st.session_state.conversation_state)
            )
        
        # --- NOWA, INTELIGENTNA LOGIKA WYŚWIETLANIA ---
        if isinstance(agent_response, list):
            # Agent zwrócił dane analityczne!
            if not agent_response:
                response_text = "Nie znalazłem żadnych danych pasujących do Twojego zapytania."
                st.markdown(response_text)
            else:
                import pandas as pd
                response_text = "Przygotowałem dla Ciebie podsumowanie."
                st.markdown(response_text)
                
                # Dynamiczne tworzenie DataFrame
                df = pd.DataFrame(agent_response)
                
                # Sprawdzamy, czy mamy dwie kolumny do wykresu
                if len(df.columns) == 2:
                    st.dataframe(df)
                    # Używamy nazw kolumn zwróconych przez SQLAlchemy
                    st.bar_chart(df, x=df.columns[1], y=df.columns[0])
                else:
                    st.dataframe(df)

            st.session_state.messages.append({"role": "assistant", "content": response_text})

        else: # Agent zwrócił zwykły tekst
            response_text = agent_response
            st.markdown(response_text)

    # Dodaj odpowiedź agenta do historii na potrzeby kolejnych interakcji
    st.session_state.messages.append({"role": "assistant", "content": response_text}) 