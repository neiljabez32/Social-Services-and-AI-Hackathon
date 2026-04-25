"""
Coordinator view.

This is a demo-only page for showing judges the other side of the flow: what
a caseworker at one of the 9 agencies in the kit sees when they look at the
data.

The point of this page is to prove our privacy gates actually work. We load
the kit's full sample data and let the judge pick a viewing org. Records are
filtered per the privacy rules.
"""

import pandas as pd
import streamlit as st

from app.privacy_gates import can_share_record, can_use_consent


@st.cache_data
def _load_all():
    return {
        "clients": pd.read_csv("data/clients_sample.csv"),
        "consents": pd.read_csv("data/consent_records_sample.csv"),
        "orgs": pd.read_csv("data/organizations_sample.csv"),
        "referrals": pd.read_csv("data/referrals_sample.csv"),
    }


def render():
    st.title("Coordinator view")
    st.caption(
        "Demo page — shows judges how the same data looks through our "
        "consent-aware filters. Not part of the applicant flow."
    )

    data = _load_all()
    orgs = data["orgs"]
    clients = data["clients"]
    consents = data["consents"]

    st.markdown("### Who are you logged in as?")
    selected_org = st.selectbox(
        "Pick an agency:",
        options=orgs["org_id"].tolist(),
        format_func=lambda x: f"{x} — {orgs[orgs.org_id == x].iloc[0].org_name}",
        index=2,  # Default to Downtown Outreach Collective
    )

    st.markdown("---")

    # Newly intaken client
    if "client" in st.session_state and st.session_state.client.first_name:
        c = st.session_state.client
        st.info(
            f"🆕 Your new intake **{c.first_name} {c.last_name}** is waiting "
            f"to be saved. Once the applicant submits, this coordinator view "
            "will reflect their consent choices."
        )

    # Full cross-agency client list, gated
    st.markdown(f"### Clients visible to `{selected_org}`")

    visible = []
    blocked = 0
    for _, row in clients.iterrows():
        allowed, reason = can_share_record(row, selected_org)
        if allowed:
            visible.append(row)
        else:
            blocked += 1

    visible_df = pd.DataFrame(visible)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total clients in system", len(clients))
    col2.metric("Visible to this agency", len(visible))
    col3.metric("Gated by OCAP / consent", blocked)

    st.caption(
        f"{blocked} records are present in the system but not visible to "
        "this agency because of OCAP protection or sharing scope restrictions. "
        "Judges: this is the kit's non-negotiable constraint #1 in action."
    )

    # Sample the visible set
    if len(visible_df) > 0:
        display_cols = [
            "client_id",
            "first_name",
            "last_name",
            "primary_org_id",
            "housing_status",
            "indigenous_identity",
            "ocap_protected",
            "consent_coverage_level",
        ]
        available = [c for c in display_cols if c in visible_df.columns]
        st.dataframe(visible_df[available].head(30), use_container_width=True)

    st.markdown("---")

    # Consent red-flag detection
    st.markdown("### Consent red flags in this data")
    st.caption(
        "The starter kit seeds red-flag patterns in the `notes` column with "
        "prefix `RED_FLAG_`. A real coordination tool should surface these."
    )

    if "notes" in consents.columns:
        red_flags = consents[consents["notes"].fillna("").str.contains("RED_FLAG_")]
        st.metric("Red flag consent records", len(red_flags))
        if len(red_flags) > 0:
            flag_summary = (
                red_flags["notes"]
                .str.extract(r"(RED_FLAG_\w+)")[0]
                .value_counts()
                .reset_index()
            )
            flag_summary.columns = ["Red flag type", "Count"]
            st.dataframe(flag_summary, use_container_width=True)

    st.markdown("---")

    # Consent usability gate demo
    st.markdown("### Active consent coverage")
    st.caption("How many consents pass our `can_use_consent` gate?")

    usable = 0
    blocked_consents = {"expired": 0, "withdrawn": 0, "missing_purpose": 0, "other": 0}
    for _, row in consents.iterrows():
        ok, reason = can_use_consent(row)
        if ok:
            usable += 1
        else:
            if "expired" in reason.lower():
                blocked_consents["expired"] += 1
            elif "withdraw" in reason.lower():
                blocked_consents["withdrawn"] += 1
            elif "purpose_codes" in reason.lower():
                blocked_consents["missing_purpose"] += 1
            else:
                blocked_consents["other"] += 1

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Usable", usable)
    c2.metric("Expired", blocked_consents["expired"])
    c3.metric("Withdrawn", blocked_consents["withdrawn"])
    c4.metric("No purpose codes", blocked_consents["missing_purpose"])
    c5.metric("Other blocks", blocked_consents["other"])

    st.caption(
        "The 'missing purpose codes' count is the FOIPPA statutory-sharing "
        "gap the kit calls out as constraint #3. Our system refuses to act "
        "on these records."
    )
