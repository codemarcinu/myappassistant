import streamlit as st
import asyncio
import sys
import os
import pandas as pd
from typing import Union, List, Dict, Any, TypedDict
import matplotlib.pyplot as plt
from backend.agents.base_agent import BaseAgent
from backend.agents.orchestrator import orchestrator
from backend.models.shopping import ShoppingTrip

# Upewnij się, że ścieżka do backendu jest poprawna
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.agents.state import ConversationState

class Message(TypedDict):
    role: str
    content: Union[str, pd.DataFrame]

# Konfiguracja strony i tytuł
st.set_page_config(page_title="FoodSave AI", layout="wide")
st.title("🤖 FoodSave AI - Twój Asystent Zakupowy")

# Inicjalizacja Pamięci Sesji
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Cześć! Jak mogę Ci pomóc?"}]
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = ConversationState()

# Wyświetlanie Historii Czatu
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        content = message["content"]
        if isinstance(content, pd.DataFrame):
            st.markdown("Przygotowałem dla Ciebie podsumowanie:")
            st.dataframe(content)
            # Sprawdzamy, czy dane nadają się na wykres
            if not content.empty and len(content.columns) == 2:
                # Upewnijmy się, że kolumna indeksu nie jest używana do wykresu
                if content.index.name in content.columns:
                    chart_data = content.reset_index()
                else:
                    chart_data = content
                st.bar_chart(chart_data, x=chart_data.columns[1], y=chart_data.columns[0])
        else:
            st.markdown(content)

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

# Sekcja przetwarzania paragonu
st.write("---")
st.subheader("Przetwarzanie Paragonu z Pliku")

# Importujemy nowe funkcje OCR
from backend.core.ocr import process_image_file, process_pdf_file

# Zmieniamy akceptowane typy plików, dodając PDF
uploaded_file = st.file_uploader(
    "Załącz plik z paragonem (jpg, png, pdf)...", 
    type=['jpg', 'jpeg', 'png', 'pdf']
)

# Sprawdzamy, czy został załadowany NOWY plik
if uploaded_file is not None and uploaded_file.name != st.session_state.get("processed_file_name"):
    with st.spinner("Przetwarzam paragon..."):
        file_bytes = uploaded_file.getvalue()
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        extracted_text = None
        if file_extension in ['jpg', 'jpeg', 'png']:
            extracted_text = process_image_file(file_bytes)
        elif file_extension == 'pdf':
            extracted_text = process_pdf_file(file_bytes)
            
        if extracted_text:
            st.success("Odczytałem tekst z paragonu!")
            st.text_area("Odczytany surowy tekst:", extracted_text, height=300)
            
            # Zapisujemy tekst ORAZ nazwę przetworzonego pliku w pamięci sesji
            st.session_state.ocr_text = extracted_text
            st.session_state.processed_file_name = uploaded_file.name
            st.info("Tekst został przygotowany. Teraz poproś agenta, aby go przetworzył, np. pisząc: 'przeanalizuj ten paragon'.")
        else:
            st.error("Nie udało się odczytać tekstu z pliku.")
            # Czyścimy nazwę, jeśli przetwarzanie się nie udało
            st.session_state.processed_file_name = None

# Pobieramy polecenie z przycisku lub z pola tekstowego
prompt = st.chat_input("Wpisz swoje polecenie...")
if "action_command" in st.session_state and st.session_state.action_command:
    prompt = st.session_state.action_command
    st.session_state.action_command = None

# Główna Pętla Interakcji
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Sprawdzamy, czy w tle nie czeka jakiś obrazek do przetworzenia
    context_from_ocr = ""
    if "ocr_text" in st.session_state and st.session_state.ocr_text:
        context_from_ocr = f"Użytkownik załączył paragon. Oto odczytany z niego tekst:\n\n---\n{st.session_state.ocr_text}\n---"
        # Czyścimy tekst z pamięci, aby nie przetwarzać go ponownie
        del st.session_state.ocr_text
    
    agent_response = asyncio.run(
        orchestrator.process_command(prompt, st.session_state.conversation_state, ocr_context=context_from_ocr)
    )
    
    response_for_history = agent_response
    
    # NOWA LOGIKA TWORZENIA DATAFRAME
    if isinstance(agent_response, list) and agent_response:
        if isinstance(agent_response[0], ShoppingTrip):
            # Obsługa listy wszystkich paragonów
            data_for_df = [{"Data": trip.trip_date, "Sklep": trip.store_name, "Kwota": trip.total_amount} for trip in agent_response]
            response_for_history = pd.DataFrame(data_for_df)
        elif isinstance(agent_response[0], tuple) or isinstance(agent_response[0], object) and hasattr(agent_response[0], '_fields'):
            # Obsługa wyników analitycznych
            response_for_history = pd.DataFrame(agent_response)
            if len(response_for_history.columns) == 2:
                response_for_history.columns = ['Wartość', 'Grupa']
                response_for_history = response_for_history.set_index('Grupa')

    st.session_state.messages.append({"role": "assistant", "content": str(response_for_history)})
    # Usuwamy st.rerun() - Streamlit automatycznie odświeży interfejs 