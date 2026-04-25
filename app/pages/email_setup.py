"""Email setup page — walkthrough for people who don't have email."""

import streamlit as st


def render():
    st.title("Step 1: Do you have an email address?")

    st.markdown(
        """
You need an email address to apply for Income Assistance. The government
sends important messages there, like when they need more information or when
your application is ready.

If you have one already, great. If not, we'll help you get one now. It's free
and takes about 5 minutes.
"""
    )

    has_email = st.radio(
        "Do you have an email address you can use?",
        options=[
            "Yes, I have one and I can check it",
            "I have one but I'm not sure I can get into it",
            "No, I don't have one",
        ],
        index=None,
        key="email_choice",
    )

    st.markdown("---")

    if has_email == "Yes, I have one and I can check it":
        email = st.text_input(
            "Type your email address here:",
            placeholder="example@gmail.com",
            key="email_input",
        )
        if email and "@" in email and "." in email.split("@")[-1]:
            st.session_state.client.email = email
            st.success("Saved. We'll use this when you apply.")
            if st.button("Next →", type="primary"):
                st.session_state.page = "intake"
                st.rerun()
        elif email:
            st.warning(
                "That doesn't look like a full email address. "
                "It should have an @ and something like .com or .ca."
            )

    elif has_email == "I have one but I'm not sure I can get into it":
        st.warning(
            "This happens a lot. Usually it's a forgotten password.\n\n"
            "You have two options:\n\n"
            "1. **Try to recover it.** Go to your email provider's website "
            "(Gmail, Outlook, Yahoo) and click 'Forgot password'.\n"
            "2. **Make a new one.** Faster if you don't remember which email "
            "it was or which password."
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("I'll try to recover it — keep my spot"):
                st.info("Come back when you have access. Your progress stays.")
        with col2:
            if st.button("Let's make a new one →"):
                st.session_state.email_choice = "No, I don't have one"
                st.rerun()

    elif has_email == "No, I don't have one":
        st.markdown("### We'll walk you through making one — free.")
        st.markdown(
            """
We recommend **Proton Mail**. It's a free email service. Unlike some others,
you do **not** need a phone number to sign up. That matters if you don't have
a steady phone.
"""
        )

        with st.expander("Step-by-step: Create a Proton Mail account", expanded=True):
            st.markdown(
                """
**1. Open a browser on this computer** and go to **proton.me/mail**

**2. Click the blue "Get Proton Free" or "Create free account" button.**

**3. Pick a username.** This will be the part of your email before the @.
Good ideas: your first name + a few numbers. Example: `janesmith47`. If the
name is taken, Proton will suggest other ones.

**4. Make a password.** Write it down on a piece of paper. You will need it
to get back into your email. If you lose this password, your email is gone.

**5. Skip the "recovery email" step.** Click "Skip" or "Maybe later". You
don't need one right now.

**6. Verify you're human.** Proton will ask you to solve a puzzle or click
some boxes. It's checking you're a real person.

**7. You're in.** Your new email is your username + `@proton.me`.
Example: `janesmith47@proton.me`.
"""
            )

        st.markdown("---")
        email = st.text_input(
            "Once you've made it, type your new email here:",
            placeholder="yourname@proton.me",
            key="email_input_new",
        )
        if email and "@" in email and "." in email.split("@")[-1]:
            st.session_state.client.email = email
            st.success("Saved. Next we'll ask a few things about you.")
            if st.button("Next →", type="primary"):
                st.session_state.page = "intake"
                st.rerun()
        elif email:
            st.warning("That doesn't look complete. Should end with something like @proton.me")

        st.markdown("---")
        st.info(
            "**If this is too much, that's okay.** Call **1-866-866-0800** "
            "and tell them you're applying for Income Assistance but don't have "
            "email. They can take a paper application over the phone."
        )
