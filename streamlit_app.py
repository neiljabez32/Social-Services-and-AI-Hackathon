"""
Intake Companion — main Streamlit entry point.

Run locally:
    streamlit run streamlit_app.py

You will need ANTHROPIC_API_KEY set, either as an environment variable or in
.streamlit/secrets.toml:

    # .streamlit/secrets.toml
    ANTHROPIC_API_KEY = "sk-ant-..."
"""

import os
import streamlit as st

# Pull secrets into environment before any module imports Anthropic client.
if "ANTHROPIC_API_KEY" in st.secrets:
    os.environ["ANTHROPIC_API_KEY"] = st.secrets["ANTHROPIC_API_KEY"]

st.set_page_config(
    page_title="Oflex",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Navigation
# -----------------------------------------------------------------------------

PAGES = {
    "Welcome": "welcome",
    "1. Email check": "email",
    "2. Tell us about you": "intake",
    "3. Your privacy choices": "consent",
    "4. Review & next steps": "review",
    "Coordinator view (demo)": "coordinator",
}

if "page" not in st.session_state:
    st.session_state.page = "welcome"

with st.sidebar:
    st.markdown("## Oflex")
    st.caption("BC Income Assistance — guided intake")
    st.markdown("---")

    for label, key in PAGES.items():
        if st.button(label, use_container_width=True, key=f"nav_{key}"):
            st.session_state.page = key
            st.rerun()

    st.markdown("---")
    st.caption(
        "Need help? Call the Ministry toll-free: **1-866-866-0800**. "
        "Interpreters available."
    )
    st.caption("You can stop any time. Nothing is submitted until you press Submit.")

# -----------------------------------------------------------------------------
# Page dispatcher
# -----------------------------------------------------------------------------

page = st.session_state.page

if page == "welcome":
    from app.pages import welcome

    welcome.render()
elif page == "email":
    from app.pages import email_setup

    email_setup.render()
elif page == "intake":
    from app.pages import intake

    intake.render()
elif page == "consent":
    from app.pages import consent

    consent.render()
elif page == "review":
    from app.pages import review

    review.render()
elif page == "coordinator":
    from app.pages import coordinator

    coordinator.render()

# -----------------------------------------------------------------------------
# Help assistant (sidebar, available on every page)
# -----------------------------------------------------------------------------

from app.help_chat import render_in_sidebar as render_help

render_help()
