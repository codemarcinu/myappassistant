from typing import Dict

import streamlit as st


def sidebar(active_agent: str, agents: Dict[str, Dict[str, str]]) -> str:
    """
    Display the sidebar with agent selection and app information.

    Args:
        active_agent: Currently selected agent
        agents: Dictionary of available agents with their details

    Returns:
        The selected agent
    """
    with st.sidebar:
        st.title("FoodSave AI")
        st.subheader("Twój asystent oszczędzania")

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

        # App information
        st.markdown("### O aplikacji")
        st.markdown(
            """
            FoodSave AI to asystent, który pomoże Ci:
            - Analizować paragony
            - Planować budżet
            - Oszczędzać na jedzeniu
            """
        )

        st.divider()
        st.caption("© 2025 FoodSave AI")

    return selected_agent
