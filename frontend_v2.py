import streamlit as st
import requests
import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

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

# Adres URL backendu
BACKEND_CHAT_URL = "http://localhost:8000/api/upload/"
BACKEND_PANTRY_URL = "http://localhost:8000/api/pantry/products" # Nowy URL

# --- Inicjalizacja Stanu Sesji ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Cześć! Jestem Twoim asystentem FoodSave. W czym mogę dziś pomóc?"}]
if "active_agent" not in st.session_state:
    st.session_state.active_agent = "budget"
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = {}

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
        chat_container = st.container()

        # Wyświetlanie historii czatu
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    if "data" in message and message["data"] is not None:
                        try:
                            df = pd.DataFrame(message["data"])
                            st.dataframe(df, use_container_width=True)
                        except Exception as e:
                            st.error(f"Nie udało się wyświetlić danych: {e}")
                            st.json(message["data"])

        # Input użytkownika
        if prompt := st.chat_input("Wpisz polecenie lub pytanie..."):
            # Dodaj wiadomość użytkownika do historii
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Wywołanie API backendu
            try:
                payload = {
                    "command": prompt,
                    "conversation_state": json.dumps(st.session_state.conversation_state)
                }
                with st.spinner("Agent myśli..."):
                    response = requests.post(BACKEND_CHAT_URL, json=payload)
                    response.raise_for_status() # Rzuć wyjątkiem dla kodów błędu 4xx/5xx
                
                response_data = response.json()
                
                # Przygotuj odpowiedź asystenta
                assistant_response_content = response_data.get("response_text", "Przepraszam, wystąpił błąd.")
                assistant_response_data = response_data.get("response_data")
                st.session_state.conversation_state = response_data.get("conversation_state", {})

                # Dodaj odpowiedź asystenta do historii
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_response_content,
                    "data": assistant_response_data
                })
                
                # Odśwież, aby wyświetlić najnowszą odpowiedź
                st.rerun()

            except requests.exceptions.RequestException as e:
                error_message = f"Błąd połączenia z backendem: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})
            except Exception as e:
                error_message = f"Wystąpił nieoczekiwany błąd: {e}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})


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

    @st.cache_data(ttl=60) # Cache na 60 sekund
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
        st.info("Twoja spiżarnia jest pusta. Dodaj produkty za pomocą czatu, np. 'dodaj paragon z wczoraj'.")
    else:
        # Można dodać filtry
        # category_filter = st.selectbox("Filtruj po kategorii", ["Wszystkie"] + sorted(list(set(p.get('unified_category', 'Inne') for p in products))))
        
        for product in products:
            # Domyślne wartości na wypadek braku danych
            name = product.get('name', 'Brak nazwy')
            category = product.get('unified_category', 'Brak kategorii')
            
            # W przyszłości można dodać datę ważności do modelu
            expiry_date_str = "Wygasa: nie podano"

            st.markdown(f"""
            <div class="product-item">
                <div class="product-info">
                    <h4>{name}</h4>
                    <p class="product-category">{category}</p>
                    <p class="product-expiry">{expiry_date_str}</p>
                </div>
                <div class="product-actions">
                    <button class="btn btn--sm btn--outline">Edytuj</button>
                    <button class="btn btn--sm btn--outline">Usuń</button>
                </div>
            </div>
            """, unsafe_allow_html=True) 