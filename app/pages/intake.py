"""
Intake page — the core low-literacy, one-question-at-a-time intake.

Hybrid design: we use a deterministic script for the core fields so the
demo is reliable, but offer an AI chat mode as an alternative where users
can describe things in their own words and the AI translates to schema values.
"""

from datetime import date

import streamlit as st

from app.schema import (
    ClientRecord,
    SLEEPING_LOCATION_PLAIN,
    INDIGENOUS_PLAIN,
    GOVERNING_NATIONS,
)
from app.ai_layer import translate_to_enum


# Script steps — deterministic order. Each step is (key, question, kind, options)
SCRIPT = [
    ("first_name", "What's your first name?", "text", None),
    ("last_name", "What's your last name?", "text", None),
    (
        "aliases_q",
        "Do you sometimes go by a different name? (nickname, former name, etc.) "
        "You can say 'no' if not.",
        "text",
        None,
    ),
    (
        "dob",
        "When were you born? If you don't know the exact day, you can type 'unknown'.",
        "date_or_unknown",
        None,
    ),
    (
        "current_sleeping_location_plain",
        "Where did you sleep last night?",
        "choice",
        list(SLEEPING_LOCATION_PLAIN.keys()) + ["Something else (I'll describe it)"],
    ),
    (
        "indigenous_identity_plain",
        "Do you identify as Indigenous? This is optional, and affects how we "
        "handle your information.",
        "choice",
        list(INDIGENOUS_PLAIN.keys()),
    ),
    (
        "phone",
        "Is there a phone number where we can reach you? Type 'none' if you "
        "don't have one right now.",
        "text",
        None,
    ),
]


def _next_step():
    st.session_state.intake_step += 1


def _save_answer(step_key, raw_value):
    """Map the plain-language answer into the schema-typed ClientRecord."""
    c: ClientRecord = st.session_state.client

    if step_key == "first_name":
        c.first_name = raw_value.strip().title()
    elif step_key == "last_name":
        c.last_name = raw_value.strip().title()
    elif step_key == "aliases_q":
        if raw_value and raw_value.strip().lower() not in ("no", "none", "n/a", ""):
            c.aliases = raw_value.strip()
    elif step_key == "dob":
        if raw_value and raw_value != "unknown":
            c.dob = raw_value
            # derive age
            try:
                from datetime import datetime as dt

                b = dt.fromisoformat(raw_value)
                today = dt.today()
                c.age = today.year - b.year - ((today.month, today.day) < (b.month, b.day))
            except Exception:
                pass
    elif step_key == "current_sleeping_location_plain":
        if raw_value in SLEEPING_LOCATION_PLAIN:
            c.current_sleeping_location = SLEEPING_LOCATION_PLAIN[raw_value]
            # Derive housing_status from sleeping location
            if c.current_sleeping_location in ("shelter", "unsheltered", "couch"):
                c.housing_status = "homeless"
            elif c.current_sleeping_location == "supportive":
                c.housing_status = "provisionally_housed"
            elif c.current_sleeping_location == "housed":
                c.housing_status = "housed"
            elif c.current_sleeping_location == "institution":
                c.housing_status = "at_risk"
        else:
            # Free text — defer to AI translation on review page
            st.session_state["_pending_sleep_text"] = raw_value
    elif step_key == "indigenous_identity_plain":
        if raw_value in INDIGENOUS_PLAIN:
            c.indigenous_identity = INDIGENOUS_PLAIN[raw_value]
    elif step_key == "phone":
        if raw_value and raw_value.strip().lower() not in ("none", "no", "n/a", ""):
            c.phone = raw_value.strip()


def render():
    st.title("Step 2: Tell us about you")

    if "intake_step" not in st.session_state:
        st.session_state.intake_step = 0

    step = st.session_state.intake_step

    # Progress indicator
    progress = step / len(SCRIPT)
    st.progress(progress, text=f"Question {min(step + 1, len(SCRIPT))} of {len(SCRIPT)}")

    if step >= len(SCRIPT):
        # Handle Indigenous follow-up
        c: ClientRecord = st.session_state.client
        if c.indigenous_identity in ("first_nations", "metis", "inuit"):
            _render_ocap_followup()
        else:
            st.success("Thanks — that's all for this part.")
            st.markdown(
                "Next we'll ask about your privacy choices. This is important: "
                "you get to decide who sees your information."
            )
            if st.button("Next: privacy choices →", type="primary"):
                st.session_state.page = "consent"
                st.rerun()
        return

    step_key, question, kind, options = SCRIPT[step]

    st.markdown(f"### {question}")

    answer = None
    if kind == "text":
        answer = st.text_input("Your answer", key=f"intake_{step_key}", label_visibility="collapsed")
        submit = st.button("Next →", type="primary", disabled=not answer)
        if submit:
            _save_answer(step_key, answer)
            _next_step()
            st.rerun()

    elif kind == "date_or_unknown":
        mode = st.radio(
            "Choose one:",
            ["I know my date of birth", "I don't know the exact date"],
            key=f"intake_{step_key}_mode",
        )
        if mode == "I know my date of birth":
            d = st.date_input(
                "Your birth date",
                value=None,
                min_value=date(1900, 1, 1),
                max_value=date.today(),
                key=f"intake_{step_key}_date",
            )
            if st.button("Next →", type="primary", disabled=d is None):
                _save_answer(step_key, d.isoformat())
                _next_step()
                st.rerun()
        else:
            st.caption("That's okay — a worker can help fill this in later.")
            if st.button("Next →", type="primary"):
                _save_answer(step_key, "unknown")
                _next_step()
                st.rerun()

    elif kind == "choice":
        answer = st.radio(
            "Pick the closest one:",
            options,
            index=None,
            key=f"intake_{step_key}",
        )
        if answer == "Something else (I'll describe it)":
            free = st.text_area(
                "Tell us in your own words:",
                key=f"intake_{step_key}_free",
            )
            if st.button("Next →", type="primary", disabled=not free):
                # Use AI to translate to enum
                with st.spinner("Got it — processing..."):
                    result = translate_to_enum(free, "current_sleeping_location")
                if result.get("value"):
                    st.session_state.client.current_sleeping_location = result["value"]
                    # derive housing_status the same way
                    sleep = result["value"]
                    if sleep in ("shelter", "unsheltered", "couch"):
                        st.session_state.client.housing_status = "homeless"
                    elif sleep == "supportive":
                        st.session_state.client.housing_status = "provisionally_housed"
                    elif sleep == "housed":
                        st.session_state.client.housing_status = "housed"
                _next_step()
                st.rerun()
        elif answer is not None:
            if st.button("Next →", type="primary"):
                _save_answer(step_key, answer)
                _next_step()
                st.rerun()

    # Back button (always available)
    st.markdown("---")
    col_back, _, col_skip = st.columns([1, 4, 1])
    with col_back:
        if step > 0 and st.button("← Back"):
            st.session_state.intake_step -= 1
            st.rerun()
    with col_skip:
        if st.button("Skip this one"):
            _next_step()
            st.rerun()


def _render_ocap_followup():
    """Extra step for Indigenous clients — governing nation and OCAP preferences."""
    c: ClientRecord = st.session_state.client

    st.markdown("### One more question")
    st.markdown(
        """
Thank you for sharing that. Because you identified as Indigenous, we want to
handle your information according to **OCAP principles** — that means your
community has a say in how your data is stored and shared.

This is your choice, not a requirement.
"""
    )

    nation = st.selectbox(
        "Which Nation or community should we contact about your data, if asked?",
        options=["I'd rather not say"] + GOVERNING_NATIONS,
        key="ocap_nation",
    )

    want_ocap = st.radio(
        "Do you want your record marked as OCAP-protected? This means other "
        "agencies can't see your file without your Nation's permission.",
        options=[
            "Yes, mark it OCAP-protected",
            "No, I don't need that",
            "I don't know — tell me more",
        ],
        index=None,
        key="ocap_choice",
    )

    if want_ocap == "I don't know — tell me more":
        st.info(
            "OCAP stands for **Ownership, Control, Access, and Possession**. "
            "It's a set of First Nations data governance principles. Marking your "
            "record OCAP-protected is a safety measure — it means agencies must "
            "get your Nation's permission before sharing your information, even "
            "for things like housing referrals. Some people want this, some don't. "
            "It's your call."
        )

    if want_ocap in ("Yes, mark it OCAP-protected", "No, I don't need that"):
        if st.button("Save and continue →", type="primary"):
            c.ocap_protected = want_ocap == "Yes, mark it OCAP-protected"
            if nation != "I'd rather not say":
                c.ocap_governing_nation = nation
            st.session_state.page = "consent"
            st.rerun()
