import streamlit as st

from ui.config import Config


def sidebar(active_agent: str, agents: dict) -> str:
    """Sidebar z ustawieniami i wyborem agenta."""
    st.sidebar.markdown(
        f"<h2>{Config.PAGE_TITLE} - Ustawienia</h2>", unsafe_allow_html=True
    )
    st.sidebar.selectbox(
        "Model AI",
        [Config.DEFAULT_MODEL, "GPT-4", "Gemini"],
        key="model_choice",
    )
    st.sidebar.toggle("Tryb kreatywny", key="creative_mode")
    st.sidebar.selectbox("Język", ["Polski", "English"], key="language")
    st.sidebar.markdown("---")
    st.sidebar.markdown("<h4>Aktywny Agent</h4>", unsafe_allow_html=True)
    selected = st.sidebar.radio(
        "Wybierz agenta:",
        options=list(agents.keys()),
        format_func=lambda agent_id: (
            f"{agents[agent_id]['icon']} {agents[agent_id]['name']}"
        ),
        key="selected_agent_radio",
    )
    return selected
