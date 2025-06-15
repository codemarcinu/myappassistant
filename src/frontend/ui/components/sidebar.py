from typing import Dict, Tuple

import streamlit as st


def sidebar(
    active_agent: str, agents: Dict[str, Dict[str, str]]
) -> Tuple[str, Dict[str, bool]]:
    """
    Display the sidebar with agent selection and app information.

    Args:
        active_agent: Currently selected agent
        agents: Dictionary of available agents with their details

    Returns:
        Tuple containing:
        - The selected agent
        - Dictionary of agent activation states
    """
    # Initialize agent states in session state if not present
    if "agent_states" not in st.session_state:
        st.session_state.agent_states = {
            "weather": True,  # Weather enabled by default
            "search": True,  # Search enabled by default
            "shopping": False,
            "cooking": False,
        }

    with st.sidebar:
        st.title("AI Assistant")
        st.subheader("Twój osobisty asystent")

        st.divider()

        # Agent selection
        st.subheader("Wybierz agenta:")
        selected_agent = active_agent

        for agent_id, agent_info in agents.items():
            icon = agent_info.get("icon", "🤖")
            name = agent_info.get("name", agent_id)

            if st.button(
                f"{icon} {name}",
                key=f"agent_{agent_id}",
                use_container_width=True,
                type="primary" if agent_id == active_agent else "secondary",
            ):
                selected_agent = agent_id

        st.divider()

        # Agent activation sliders
        st.subheader("Włącz/wyłącz agenty:")

        # Weather agent slider
        weather_enabled = st.slider(
            "🌤️ Prognoza pogody",
            min_value=0,
            max_value=1,
            value=1 if st.session_state.agent_states["weather"] else 0,
            step=1,
            format=None,
            key="weather_slider",
            label_visibility="visible",
        )
        st.session_state.agent_states["weather"] = bool(weather_enabled)

        # Search agent slider
        search_enabled = st.slider(
            "🔍 Wyszukiwanie",
            min_value=0,
            max_value=1,
            value=1 if st.session_state.agent_states["search"] else 0,
            step=1,
            format=None,
            key="search_slider",
            label_visibility="visible",
        )
        st.session_state.agent_states["search"] = bool(search_enabled)

        # Shopping agent slider
        shopping_enabled = st.slider(
            "🛒 Zakupy",
            min_value=0,
            max_value=1,
            value=1 if st.session_state.agent_states["shopping"] else 0,
            step=1,
            format=None,
            key="shopping_slider",
            label_visibility="visible",
        )
        st.session_state.agent_states["shopping"] = bool(shopping_enabled)

        # Cooking agent slider
        cooking_enabled = st.slider(
            "👨‍🍳 Gotowanie",
            min_value=0,
            max_value=1,
            value=1 if st.session_state.agent_states["cooking"] else 0,
            step=1,
            format=None,
            key="cooking_slider",
            label_visibility="visible",
        )
        st.session_state.agent_states["cooking"] = bool(cooking_enabled)

        st.divider()

        # App information
        st.markdown("### O aplikacji")
        st.markdown(
            """
            Asystent AI pomoże Ci:
            - Wyszukiwać informacje
            - Sprawdzać pogodę
            - Planować zakupy
            - Doradzać w gotowaniu
            """
        )

        st.divider()
        st.caption("© 2025 AI Assistant")

    return selected_agent, st.session_state.agent_states
