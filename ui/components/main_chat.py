from typing import Any, Dict, List

import streamlit as st


def main_chat(
    messages: List[Dict[str, Any]], loading: bool = False, error: str = ""
) -> None:
    """Wyświetla główny czat z wiadomościami, loading i error."""
    chat_container = st.container()
    with chat_container:
        for message in messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if "data" in message and message["data"] is not None:
                    st.json(message["data"])
        if loading:
            st.info("Ładowanie odpowiedzi agenta...")
        if error:
            st.error(error)
