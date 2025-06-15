from typing import Any, Dict, List

import streamlit as st


def main_chat(messages: List[Dict[str, Any]], loading: bool, error: str) -> None:
    """
    Display the main chat interface with message history.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        loading: Boolean indicating if the system is processing a request
        error: Error message to display (if any)
    """
    # Display error if any
    if error:
        st.error(f"Błąd: {error}")

    # Display loading indicator
    if loading:
        with st.spinner("Przetwarzam..."):
            st.info("Asystent odpowiada...")

    # Display chat messages
    for msg in messages:
        role = msg.get("role", "")
        content = msg.get("content", "")
        data = msg.get("data")

        if role == "user":
            st.chat_message("user").write(content)
        elif role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(content)  # Use markdown for better formatting

                # Display any data that came with the message
                if data:
                    if isinstance(data, list) and len(data) > 0:
                        st.json(data)
                    elif isinstance(data, dict) and data:
                        st.json(data)

    # Add debug information
    if messages:
        st.caption(f"Debug: {len(messages)} messages in conversation")
