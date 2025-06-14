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
        
        # --- ULEPSZONA LOGIKA WYŚWIETLANIA Z KOMPONENTAMI STREAMLIT ---
        
        # Domyślnie używamy st.markdown
        display_function = st.markdown
        response_text_for_history = ""

        if isinstance(agent_response, list):
            # Agent zwrócił dane analityczne
            if not agent_response:
                response_text_for_history = "Nie znalazłem żadnych danych pasujących do Twojego zapytania."
                st.warning(response_text_for_history) # Używamy st.warning dla "nie znaleziono"
            else:
                import pandas as pd
                response_text_for_history = "Przygotowałem dla Ciebie podsumowanie."
                st.success(response_text_for_history) # Używamy st.success dla powodzenia
                
                try:
                    df = pd.DataFrame(agent_response)
                    # Sprawdzamy, czy mamy dwie kolumny do wykresu
                    if len(df.columns) == 2:
                        st.dataframe(df)
                        # Używamy nazw kolumn zwróconych przez SQLAlchemy
                        st.bar_chart(df, x=df.columns[1], y=df.columns[0])
                    else:
                        st.dataframe(df)
                except Exception as e:
                    st.error(f"Wystąpił błąd podczas tworzenia wykresu: {e}")

        else: # Agent zwrócił zwykły tekst
            response_text_for_history = agent_response
            # Wybieramy komponent na podstawie słów kluczowych w odpowiedzi
            if "Gotowe" in response_text_for_history or "Pomyślnie" in response_text_for_history:
                st.success(response_text_for_history)
            elif "Niestety" in response_text_for_history or "Błąd" in response_text_for_history:
                st.error(response_text_for_history)
            elif "pytanie" in response_text_for_history.lower() or "wybierz jedną" in response_text_for_history.lower():
                st.info(response_text_for_history) # Używamy st.info dla pytań
            else:
                st.markdown(response_text_for_history)

    # Dodaj odpowiedź agenta do historii na potrzeby kolejnych interakcji
    st.session_state.messages.append({"role": "assistant", "content": response_text_for_history}) 