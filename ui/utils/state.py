from typing import Any

import streamlit as st


def get_state(key: str, default: Any = None) -> Any:
    """Pobiera wartość ze stanu sesji lub ustawia domyślną."""
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def set_state(key: str, value: Any) -> None:
    """Ustawia wartość w stanie sesji."""
    st.session_state[key] = value
