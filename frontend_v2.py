import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

BACKEND_CHAT_URL = "http://localhost:8000/api/orchestrator/execute"
BACKEND_PANTRY_URL = "http://localhost:8000/api/pantry/products" # Nowy URL

def execute_command(command: str):
    """Wysyła polecenie do backendu i aktualizuje stan czatu."""
    st.session_state.messages.append({"role": "user", "content": command})
    try:
        payload = {
            "task": command,
            "conversation_state": st.session_state.conversation_state
        }
        with st.spinner("Agent wykonuje akcję..."):
            response = requests.post(BACKEND_CHAT_URL, json=payload)
            response.raise_for_status()
        
        response_data = response.json()
        assistant_response_content = response_data.get("response", "Przepraszam, wystąpił błąd.")
        assistant_response_data = response_data.get("data")
        
        # Aktualizujemy stan konwersacji
        st.session_state.conversation_state = response_data.get("conversation_state", {})
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": assistant_response_content,
            "data": assistant_response_data
        })
        # Wyczyść cache danych spiżarni, aby wymusić odświeżenie
        st.cache_data.clear()

    except Exception as e:
        error_message = f"Wystąpił błąd: {e}"
        st.error(error_message)
        st.session_state.messages.append({"role": "assistant", "content": error_message})

# --- Konfiguracja strony ---
st.set_page_config(
    layout="wide",
    page_title="FoodSave AI",
    page_icon="🤖"
)

# --- Ładowanie i Wstrzykiwanie CSS ---
def load_css(file_path):
    """Wczytuje plik CSS i zwraca jego zawartość."""
    with open(file_path) as f:
        return f.read()

# Upewnij się, że plik style.css jest w tym samym katalogu lub podaj poprawną ścieżkę
css_file = Path(__file__).parent / "frontend/src/style.css"
if css_file.exists():
    st.markdown(f'<style>{load_css(css_file)}</style>', unsafe_allow_html=True)
else:
    st.warning("Nie znaleziono pliku style.css. Interfejs może nie wyglądać zgodnie z oczekiwaniami.")

# --- Inicjalizacja Stanu Sesji ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?"}]
if "active_agent" not in st.session_state:
    st.session_state.active_agent = "budget"
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {}
# NOWY STAN: do obsługi akcji z przycisków
if "action_command" not in st.session_state:
    st.session_state.action_command = None

# --- Definicje Agentów ---
agents = {
    "parser": {"name": "Parser Paragonów", "icon": "📄"},
    "analyst": {"name": "Analityk Wydatków", "icon": "📊"},
    "budget": {"name": "Doradca Budżetowy", "icon": "💰"},
    "planner": {"name": "Planista Posiłków", "icon": "🍽️"},
    "sql": {"name": "Asystent SQL", "icon": "🔍"},
}

# --- Layout Aplikacji ---

# 1. Boczny Panel (Sidebar) z Ustawieniami
with st.sidebar:
    st.markdown("<h2>Globalne Ustawienia</h2>", unsafe_allow_html=True)
    
    with st.expander("🤖 Ustawienia AI", expanded=True):
        st.selectbox("Model AI", ["Llama3 (Ollama)", "GPT-4", "Gemini"], key="model_choice")
        st.toggle("Tryb kreatywny", key="creative_mode")

    with st.expander("🌍 Język i Region", expanded=False):
        st.selectbox("Język", ["Polski", "English"], key="language")

    with st.expander("🔔 Powiadomienia", expanded=False):
        st.toggle("Powiadomienia email", key="email_notify")
        st.toggle("Powiadomienia push", key="push_notify")

# 2. Główna Zawartość z Zakładkami
main_content = st.container()

with main_content:
    chat_tab, pantry_tab = st.tabs(["Czat z AI", "Moja Spiżarnia"])

    # --- Zakładka "Czat z AI" ---
    with chat_tab:
        chat_container = st.container(height=600, border=False)
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "data" in message and message["data"] is not None:
                        try:
                            df = pd.DataFrame(message["data"])
                            st.dataframe(df, use_container_width=True)
                        except Exception:
                            st.json(message["data"])

        # Input użytkownika
        if prompt := st.chat_input("Wpisz polecenie lub pytanie..."):
            execute_command(prompt)
            st.rerun() # Odśwież widok od razu po wysłaniu

    # --- Zakładka "Moja Spiżarnia" (Placeholder) ---
    with pantry_tab:
        st.markdown("<h3>Produkty w Spiżarni</h3>", unsafe_allow_html=True)
        st.info("Ta sekcja jest w budowie. W przyszłości będzie tutaj interaktywna lista produktów z Twojej spiżarni.")

        # Przykładowe dane
        st.markdown("""
        <div class="product-item">
            <div class="product-info">
                <h4>Mleko Łaciate</h4>
                <p class="product-category">Nabiał</p>
                <p class="product-expiry">Wygasa: 2025-06-20</p>
            </div>
            <div class="product-actions">
                <button class="btn btn--sm btn--outline">Edytuj</button>
                <button class="btn btn--sm btn--outline">Usuń</button>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- Sidebar: interaktywny wybór agenta ---
with st.sidebar:
    st.markdown("---")
    st.markdown("<h4>Aktywny Agent</h4>", unsafe_allow_html=True)
    active_agent_name = st.radio(
        "Wybierz agenta:",
        options=list(agents.keys()),
        format_func=lambda agent_id: f"{agents[agent_id]['icon']} {agents[agent_id]['name']}",
        key="selected_agent_radio"
    )
    if st.session_state.active_agent != active_agent_name:
        st.session_state.active_agent = active_agent_name
        st.rerun()

# --- ZAKTUALIZOWANA ZAKŁADKA "Moja Spiżarnia" ---
with pantry_tab:
    st.markdown("<h3>Produkty w Spiżarni</h3>", unsafe_allow_html=True)

    @st.cache_data(ttl=10) # Cache na 10 sekund, aby zmiany były szybko widoczne
    def get_pantry_products() -> List[Dict[str, Any]]:
        """Pobiera produkty z backendu."""
        try:
            response = requests.get(BACKEND_PANTRY_URL)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Nie udało się połączyć z backendem: {e}")
            return []
        except json.JSONDecodeError:
            st.error("Otrzymano nieprawidłowe dane z serwera.")
            return []

    products = get_pantry_products()

    if not products:
        st.info("Twoja spiżarnia jest pusta. Dodaj produkty za pomocą czatu.")
        if st.button("Odśwież listę"):
            st.cache_data.clear()
            st.rerun()
    else:
        # Nagłówki dla naszej tabeli
        col1, col2, col3 = st.columns([4, 4, 2])
        with col1:
            st.markdown("**Produkt**")
        with col2:
            st.markdown("**Kategoria**")
        with col3:
            st.markdown("**Akcje**")
        
        st.markdown("---")

        for product in products:
            name = product.get('name', 'Brak nazwy')
            category = product.get('unified_category', 'Brak kategorii')
            product_id = product.get('id')

            col1, col2, col3 = st.columns([4, 4, 2])
            
            with col1:
                st.markdown(f"**{name}**")
                st.caption(f"ID: {product_id}")
            
            with col2:
                st.markdown(category)

            with col3:
                # Przycisk Edytuj (na razie nieaktywny)
                st.button("Edytuj", key=f"edit_{product_id}", disabled=True)
                
                # Przycisk Usuń
                if st.button("Usuń", key=f"delete_{product_id}", type="secondary"):
                    # Używamy ID produktu do precyzyjnego polecenia
                    # Agent najlepiej poradzi sobie z poleceniem, które zawiera ID
                    command = f"usuń produkt o id {product_id}"
                    st.session_state.action_command = command
                    st.rerun()

# --- GŁÓWNA LOGIKA APLIKACJI ---

# NOWA SEKCJA: Sprawdzenie i wykonanie akcji z przycisku
if st.session_state.action_command:
    command_to_run = st.session_state.action_command
    st.session_state.action_command = None  # Wyzeruj natychmiast, aby uniknąć powtórzenia
    execute_command(command_to_run)
    # Nie ma potrzeby st.rerun(), bo zmiana w `messages` i tak go wywoła na końcu skryptu 