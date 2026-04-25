"""
Help chat widget.

Renders a collapsible chat assistant in the sidebar of any page.
Strictly scoped via the system prompt in app/ai_layer.HELP_SYSTEM —
refuses life advice, off-topic questions, and crisis-routes to 9-8-8.
"""

import streamlit as st

from app.ai_layer import help_chat_response


SUGGESTED_QUESTIONS = [
    "I don't have a SIN card",
    "What if I don't have an address?",
    "What's a BCeID?",
    "I don't know my date of birth exactly",
    "Can someone help me in person?",
]


def render_in_sidebar():
    """Drop this in the sidebar of any page that wants the help assistant."""
    if "help_history" not in st.session_state:
        st.session_state.help_history = []

    with st.sidebar:
        st.markdown("---")
        with st.expander("💬 Need help? Ask the assistant", expanded=False):
            st.caption(
                "I can answer questions about using Oflex and applying for "
                "Income Assistance. I won't give life or medical advice — for "
                "that, please call the right service."
            )

            # Show conversation history
            for msg in st.session_state.help_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            # Suggested questions (only when there's no history)
            if not st.session_state.help_history:
                st.caption("Common questions:")
                for q in SUGGESTED_QUESTIONS:
                    if st.button(q, key=f"suggest_{q}", use_container_width=True):
                        _send_message(q)
                        st.rerun()

            # Free text input
            user_input = st.chat_input("Type your question...", key="help_input")
            if user_input:
                _send_message(user_input)
                st.rerun()

            # Reset
            if st.session_state.help_history:
                if st.button("Clear conversation", key="clear_help"):
                    st.session_state.help_history = []
                    st.rerun()


def _send_message(text: str):
    """Append a user message, get the assistant's reply, append it."""
    history = st.session_state.help_history
    history.append({"role": "user", "content": text})
    with st.spinner("Thinking..."):
        reply = help_chat_response(history[:-1], text)
    history.append({"role": "assistant", "content": reply})
    st.session_state.help_history = history
