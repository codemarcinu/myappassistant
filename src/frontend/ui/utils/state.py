from typing import Any, Optional, TypeVar

import streamlit as st

T = TypeVar("T")


def get_state(key: str, default_value: Optional[T] = None) -> T:
    """
    Get a value from the Streamlit session state, initializing it if not present.

    Args:
        key: The key to retrieve from session state
        default_value: The default value to use if the key doesn't exist

    Returns:
        The value from session state
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]


def set_state(key: str, value: Any) -> None:
    """
    Set a value in the Streamlit session state.

    Args:
        key: The key to set in session state
        value: The value to assign
    """
    st.session_state[key] = value


def clear_state() -> None:
    """
    Clear all keys from the Streamlit session state.
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
