import os
import sys
from typing import Any, Dict, List

import requests  # type: ignore
import streamlit as st

# Add the 'src' directory to the Python path to allow absolute imports
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
)

# Import app-specific modules after path setup
from src.frontend.ui.components.data_display import data_display  # noqa: E402
from src.frontend.ui.components.main_chat import main_chat  # noqa: E402
from src.frontend.ui.components.sidebar import sidebar  # noqa: E402
from src.frontend.ui.services.api_client import ApiClient  # noqa: E402
from src.frontend.ui.utils.state import get_state, set_state  # noqa: E402


class AssistantUI:
    """Główny kontroler aplikacji Asystenta AI."""

    def __init__(self) -> None:
        self.api = ApiClient()
        self.agents = {
            "budget": {"name": "Doradca Budżetowy", "icon": "💰"},
            "weather": {"name": "Pogoda", "icon": "🌤️"},
            "search": {"name": "Wyszukiwarka", "icon": "🔍"},
            "shopping": {"name": "Zakupy", "icon": "🛒"},
            "cooking": {"name": "Gotowanie", "icon": "👨‍🍳"},
        }
        self.init_state()
        st.set_page_config(
            layout="wide",
            page_title="AI Assistant",
            page_icon="🤖",
        )

    def init_state(self) -> None:
        get_state(
            "messages",
            [
                {
                    "role": "assistant",
                    "content": (
                        "Cześć! Jestem Twoim asystentem FoodSave. "
                        "W czym mogę dziś pomóc?"
                    ),
                }
            ],
        )
        get_state("active_agent", "budget")
        get_state("conversation_state", {})
        get_state("action_command", None)
        get_state("loading", False)
        get_state("error", "")

    def run(self) -> None:
        # Get active agent and agent states from sidebar
        active_agent, agent_states = sidebar(st.session_state.active_agent, self.agents)

        # Update session state if active agent changed
        if st.session_state.active_agent != active_agent:
            set_state("active_agent", active_agent)
            st.rerun()

        # Store agent states in session state
        if "agent_states" not in st.session_state:
            set_state("agent_states", agent_states)
        elif st.session_state.agent_states != agent_states:
            set_state("agent_states", agent_states)
        main_content = st.container()
        with main_content:
            st.write("Debug: Rendering tabs")  # Debug line
            chat_tab, pantry_tab, receipt_tab = st.tabs(
                ["Czat z AI", "Moja Spiżarnia", "Paragony"]
            )
            st.write(
                f"Debug: Tab count: {len([chat_tab, pantry_tab, receipt_tab])}"
            )  # Debug line
            with chat_tab:
                main_chat(
                    st.session_state.messages,
                    st.session_state.loading,
                    st.session_state.error,
                )
                if prompt := st.chat_input("Wpisz polecenie lub pytanie..."):
                    self.handle_command(prompt)
            with pantry_tab:
                products = self.get_products()
                data_display(products)
            with receipt_tab:
                self.handle_receipt_upload()

    def handle_command(self, command: str) -> None:
        set_state("loading", True)
        set_state("error", "")
        st.session_state.messages.append({"role": "user", "content": command})

        # Get active agent states
        agent_states = st.session_state.get(
            "agent_states",
            {
                "weather": True,
                "search": True,
                "shopping": False,
                "cooking": False,
            },
        )

        payload = {
            "task": command,
            "conversation_state": st.session_state.conversation_state,
            "agent_states": agent_states,
        }
        response = self.api.post(
            "/api/v1/agents/execute",
            json=payload,
        )
        if "error" in response:
            set_state("error", response["error"])
        else:
            assistant_response_content = response.get(
                "response", "Przepraszam, wystąpił błąd."
            )
            assistant_response_data = response.get("data")
            st.session_state.conversation_state = response.get("conversation_state", {})
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": assistant_response_content,
                    "data": assistant_response_data,
                }
            )
        set_state("loading", False)
        st.rerun()

    def get_products(self) -> List[Dict[str, Any]]:
        response = self.api.get("/api/v1/pantry/products")
        if "error" in response:
            set_state("error", response["error"])
            return []
        # Ensure we're returning a list of products
        if isinstance(response, list):
            return response
        # If the API returns the products wrapped in an object
        if isinstance(response, dict) and "products" in response:
            return response["products"]
        # Return empty list as fallback
        set_state("error", "Unexpected API response format")
        return []

    def handle_receipt_upload(self) -> None:
        """Handles receipt image upload and processing."""
        uploaded_file = st.file_uploader(
            "Wgraj paragon",
            type=["jpg", "jpeg", "png", "pdf"],
            accept_multiple_files=False,
        )

        if uploaded_file is not None:
            with st.spinner("Przetwarzam paragon..."):
                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type,
                        )
                    }
                    response = requests.post(
                        "http://localhost:8000/api/v1/receipts/upload", files=files
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("Pomyślnie przetworzono paragon!")
                        st.text_area(
                            "Wyodrębniony tekst:", value=result["text"], height=300
                        )
                    else:
                        st.error(
                            f"Błąd przetwarzania: {response.json().get('detail', 'Nieznany błąd')}"
                        )
                except Exception as e:
                    st.error(f"Wystąpił błąd: {str(e)}")


if __name__ == "__main__":
    ui = AssistantUI()
    ui.run()
