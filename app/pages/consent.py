"""
Consent page.

This is where we honor PIPA/FOIPPA/OCAP in a form the applicant actually
understands. The plain-language choices map directly to sharing_scope_type
enum values from the kit's schema.
"""

from datetime import date, timedelta
import uuid

import streamlit as st

from app.schema import (
    ConsentRecord,
    SHARING_SCOPE_PLAIN,
    PURPOSE_CODES,
    DATA_CATEGORIES,
)
from app.privacy_gates import validate_consent_before_save


def render():
    st.title("Step 3: Your privacy choices")

    st.markdown(
        """
You're almost done. Before we save anything, you get to decide who can see
the information you just shared.

**Your choice. Not ours.**
"""
    )

    st.markdown("### Who can see your information?")

    scope_plain = st.radio(
        "Pick the one that feels right to you:",
        options=list(SHARING_SCOPE_PLAIN.keys()),
        index=None,
        key="scope_choice",
    )

    if scope_plain:
        scope_enum = SHARING_SCOPE_PLAIN[scope_plain]
        if scope_enum == "none":
            st.warning(
                "You've chosen not to share with anyone. That means workers at "
                "other agencies — including your housing worker or food bank — "
                "won't be able to look up your file. That's okay if that's what "
                "you want."
            )
        elif scope_enum == "org":
            st.info(
                "Only the Ministry of Social Development will see this file. "
                "No other agency gets a copy."
            )
        elif scope_enum == "cluster":
            st.info(
                "Agencies you've already worked with, where there's already a "
                "sharing agreement, can see your file. Agencies you haven't "
                "worked with will not."
            )
        elif scope_enum == "ca_table":
            st.info(
                "Agencies helping coordinate housing and support can see your "
                "file. This usually speeds things up when you need referrals."
            )

    st.markdown("---")
    st.markdown("### Why do you want us to use your information?")
    st.caption(
        "You can pick more than one. This helps us make sure your information "
        "is only used for the reasons you said yes to."
    )

    purposes_plain = {
        "To help with my application for assistance": "case_mgmt",
        "To connect me with housing or other services": "coordinated_access",
        "To make a referral to another agency when I need one": "referral",
        "For the Ministry's own reports (not shared outside)": "reporting",
        "To plan for my safety in a crisis": "safety_planning",
    }

    selected_purposes = []
    for label, code in purposes_plain.items():
        if st.checkbox(label, key=f"purpose_{code}", value=(code == "case_mgmt")):
            selected_purposes.append(code)

    st.markdown("---")
    st.markdown("### What kind of information are you sharing?")
    st.caption("Only the things you checked will be included.")

    categories_plain = {
        "Basic information (name, age, contact)": "demographics",
        "Where I'm staying right now": "demographics",
        "My mental health history": "mental_health",
        "My substance use history": "substance_use",
        "My medical history": "medical",
        "My family and children": "family",
        "My financial situation": "financial",
    }

    selected_categories = set()
    selected_categories.add("demographics")  # always needed
    for label, code in categories_plain.items():
        if code in ("demographics",):
            continue  # implicit
        if st.checkbox(label, key=f"cat_{code}"):
            selected_categories.add(code)

    st.markdown("---")
    st.markdown("### Your signature")
    signed_name = st.text_input(
        "Type your full name to sign this consent:",
        key="consent_signature",
        placeholder="Type your first and last name",
    )

    client_name = (
        f"{st.session_state.client.first_name} {st.session_state.client.last_name}".strip()
    )
    signature_matches = (
        signed_name and signed_name.strip().lower() == client_name.lower()
    )

    if signed_name and not signature_matches:
        st.warning(
            f"That doesn't match the name you gave earlier ({client_name}). "
            "Is that intentional? You can fix it or continue."
        )

    can_save = bool(scope_plain and selected_purposes and signed_name)

    if st.button("Save my privacy choices →", type="primary", disabled=not can_save):
        # Build the ConsentRecord
        c = st.session_state.client
        consent = ConsentRecord(
            consent_id=f"CNS-NEW-{uuid.uuid4().hex[:6].upper()}",
            client_id=c.client_id or f"CLI-NEW-{uuid.uuid4().hex[:4].upper()}",
            collecting_org_id="ORG-MSD",  # synthetic id representing the Ministry
            consent_type="explicit",
            status="active",
            legal_basis="consent",
            purpose_codes=";".join(selected_purposes),
            data_categories=";".join(sorted(selected_categories)),
            sharing_scope_type=SHARING_SCOPE_PLAIN[scope_plain],
            given_date=date.today().isoformat(),
            effective_date=date.today().isoformat(),
            expiry_date=(date.today() + timedelta(days=365)).isoformat(),
            consent_source="digital_signature",
            notes=f"Oflex self-serve intake. Signed as: {signed_name}",
        )

        # Link the client record
        if not c.client_id:
            c.client_id = consent.client_id
        c.current_consent_id = consent.consent_id
        c.consent_coverage_level = "explicit"
        c.default_sharing_scope = consent.sharing_scope_type

        # Run privacy gate validation
        errors = validate_consent_before_save(consent)
        if errors:
            st.error("Can't save yet — some things are missing:")
            for e in errors:
                st.error(f"• {e}")
            return

        st.session_state.consent = consent
        st.success("Saved. Your privacy choices are locked in.")
        st.session_state.page = "review"
        st.rerun()
