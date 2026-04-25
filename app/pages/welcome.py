"""Welcome page — sets expectations and offers off-ramps."""

import streamlit as st

from app.schema import ClientRecord, ConsentRecord


def render():
    st.title("Welcome")

    st.markdown(
        """
You may be here because you want to apply for **BC Income Assistance** and
someone told you this tool could help.

Here's what we'll do, together, at your pace:

1. **Check that you have an email address.** You need one to apply. If you
   don't, we'll help you get one for free.
2. **Collect a few things about you.** Name, where you stayed last night, that
   kind of thing. You can answer in your own words.
3. **Ask your permission** for what we do with your answers.
4. **Give you a summary** to take to a Ministry worker, or to use when you fill
   out the real application at **myselfserve.gov.bc.ca**.

We do not submit anything for you. You decide what happens next.
"""
    )

    st.info(
        "**You can stop any time.** If this is too much, call **1-866-866-0800** "
        "and a real person will help you. Ask for help in any language — "
        "interpreters are free."
    )

    st.markdown("---")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("Let's start →", type="primary", use_container_width=True):
            # Initialize state
            if "client" not in st.session_state:
                st.session_state.client = ClientRecord()
            if "consent" not in st.session_state:
                st.session_state.consent = ConsentRecord()
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []
            st.session_state.page = "email"
            st.rerun()

    with col2:
        st.caption(
            "Your information stays on this computer until you decide to share "
            "it. Nothing is sent anywhere without your permission."
        )
