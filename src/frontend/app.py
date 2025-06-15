from typing import Any, Dict, List

import streamlit as st
from ui.components.data_display import data_display
from ui.components.main_chat import main_chat
from ui.components.sidebar import sidebar
from ui.config import Config
from ui.services.api_client import ApiClient
from ui.utils.state import get_state, set_state


class FoodSaveUI:
    """Główny kontroler aplikacji FoodSave AI."""

    def __init__(self) -> None:
        self.api = ApiClient()
        self.agents = {
            "parser": {"name": "Parser Paragonów", "icon": "📄"},
            "analyst": {"name": "Analityk Wydatków", "icon": "📊"},
            "budget": {"name": "Doradca Budżetowy", "icon": "💰"},
            "planner": {"name": "Planista Posiłków", "icon": "🍽️"},
            "sql": {"name": "Asystent SQL", "icon": "🔍"},
        }
        self.init_state()
        st.set_page_config(
            layout="wide",
            page_title=Config.PAGE_TITLE,
            page_icon=Config.PAGE_ICON,
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
        active_agent = sidebar(st.session_state.active_agent, self.agents)
        if st.session_state.active_agent != active_agent:
            set_state("active_agent", active_agent)
            st.rerun()
        main_content = st.container()
        with main_content:
            chat_tab, pantry_tab = st.tabs(["Czat z AI", "Moja Spiżarnia"])
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

    def handle_command(self, command: str) -> None:
        set_state("loading", True)
        set_state("error", "")
        st.session_state.messages.append({"role": "user", "content": command})
        payload = {
            "task": command,
            "conversation_state": st.session_state.conversation_state,
        }
        response = self.api.post(
            "/api/orchestrator/execute",
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
        response = self.api.get("/api/pantry/products")
        if "error" in response:
            set_state("error", response["error"])
            return []
        return response


if __name__ == "__main__":
    ui = FoodSaveUI()
    ui.run()
