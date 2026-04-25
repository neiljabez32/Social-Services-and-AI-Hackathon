"""
Review page — the payoff.

Shows the applicant a plain-language summary of everything collected, then
runs the consent-aware duplicate check against the kit's existing client
table. Finally, gives them a takeaway sheet to bring to a worker or use
when filling out MySelfServe.
"""

from dataclasses import asdict

import pandas as pd
import streamlit as st

from app.duplicate_detector import find_potential_duplicates
from app.privacy_gates import can_display_duplicate_match
from app.ai_layer import summarize_intake


@st.cache_data
def _load_existing_clients():
    return pd.read_csv("data/clients_sample.csv")


def render():
    st.title("Step 4: Review and next steps")

    c = st.session_state.client
    cns = st.session_state.consent

    st.markdown("### Here's what we have")

    summary_col, sidebar_col = st.columns([2, 1])

    with summary_col:
        # Plain-language AI summary
        with st.spinner("Putting it together..."):
            try:
                summary_text = summarize_intake(asdict(c))
            except Exception as e:
                summary_text = f"(Summary unavailable — {e})"
        st.markdown(summary_text)

    with sidebar_col:
        st.markdown("**Your privacy choices**")
        scope_labels = {
            "none": "No sharing",
            "org": "Ministry only",
            "cluster": "Agencies with existing agreements",
            "ca_table": "Housing & coordination network",
            "named_agencies": "Specific agencies only",
        }
        st.markdown(f"Scope: **{scope_labels.get(cns.sharing_scope_type, cns.sharing_scope_type)}**")
        st.markdown(f"Status: `{cns.status}`")
        st.markdown(f"Expires: {cns.expiry_date}")
        if c.ocap_protected:
            st.success("🛡️ OCAP-protected")
            if c.ocap_governing_nation:
                st.caption(f"Nation: {c.ocap_governing_nation}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Consent-aware duplicate detection
    # ------------------------------------------------------------------
    st.markdown("### Is this your first time applying?")
    st.caption(
        "We checked if a file with similar information already exists in the "
        "coordination system. Whether we show you the match depends on your "
        "privacy choices."
    )

    with st.spinner("Checking..."):
        existing = _load_existing_clients()
        matches = find_potential_duplicates(c, existing, threshold=0.55)

    if not matches:
        st.info(
            "No matches found. This looks like a new file. A Ministry worker "
            "will create your official record when you submit the application."
        )
    else:
        # Apply consent gate to each match
        gated_matches = []
        blocked_matches = []
        for score, reasons, row in matches[:5]:
            allowed, gate_reason = can_display_duplicate_match(row, c, cns)
            if allowed:
                gated_matches.append((score, reasons, row))
            else:
                blocked_matches.append(gate_reason)

        if gated_matches:
            st.warning(
                f"We found **{len(gated_matches)} possible match(es)** in the system. "
                "Your privacy settings allow us to show them. Review below."
            )
            for i, (score, reasons, row) in enumerate(gated_matches):
                with st.expander(
                    f"Match {i + 1}: {row['first_name']} {row['last_name']} "
                    f"(confidence {score:.0%})"
                ):
                    st.markdown(f"**Client ID:** `{row['client_id']}`")
                    st.markdown(f"**Primary agency:** `{row['primary_org_id']}`")
                    if not pd.isna(row.get("dob")):
                        st.markdown(f"**DOB on file:** {row['dob']}")
                    if not pd.isna(row.get("aliases")) and row.get("aliases"):
                        st.markdown(f"**Aliases on file:** {row['aliases']}")
                    st.markdown("**Why we think this might be you:**")
                    for r in reasons:
                        st.markdown(f"• {r}")

                    choice = st.radio(
                        "Is this you?",
                        ["Yes — this is me, please merge", "No — this is someone else"],
                        index=None,
                        key=f"dedupe_choice_{i}",
                    )
                    if choice == "Yes — this is me, please merge":
                        st.info(
                            "Noted. A Ministry worker will review the merge "
                            "before it happens. Your privacy choices from "
                            "today will apply to the merged file."
                        )
                    elif choice == "No — this is someone else":
                        st.info(
                            "Noted. This looks like a coincidental name match. "
                            "The worker will create a separate file for you."
                        )
        elif blocked_matches:
            st.info(
                "📋 **There may be a related record on file, but we can't show "
                "it to you here.** Your privacy settings, or the other record's "
                "settings, require a coordinator with proper authorization to "
                "review the match safely. A Ministry worker can look into it."
            )
            with st.expander("Why can't I see the match?"):
                for reason in blocked_matches[:3]:
                    st.caption(f"• {reason}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Takeaway sheet
    # ------------------------------------------------------------------
    st.markdown("### Next steps")

    st.markdown(
        """
**You have two ways to finish your application:**

1. **Take this summary to a Ministry worker.** They can help you fill out the
   real MySelfServe form using what we've gathered. Print this page, or show it
   on your phone.

2. **Do it yourself at myselfserve.gov.bc.ca.** You'll need to make a BCeID
   account first using the email you gave us. The official application will
   ask similar questions — your answers here will line up.

Either way, the Ministry phone line is **1-866-866-0800** if you get stuck.
"""
    )

    # Download summary as PDF
    from app.pdf_summary import build_summary_pdf

    pdf_bytes = build_summary_pdf(c, cns)
    fname_safe = (c.first_name or "applicant").lower().replace(" ", "_")
    lname_safe = (c.last_name or "").lower().replace(" ", "_")
    pdf_filename = f"oflex_summary_{fname_safe}_{lname_safe}.pdf".replace("__", "_")

    st.download_button(
        "📄 Download my summary (PDF)",
        data=pdf_bytes,
        file_name=pdf_filename,
        mime="application/pdf",
        type="primary",
    )

    st.markdown("---")
    st.caption(
        "Nothing is submitted to the government from this page. This is your "
        "copy. When you're ready, a worker will use it to complete your official "
        "MySelfServe application."
    )
