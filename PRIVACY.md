# Privacy & Safety Statement

> **Track:** Inter-Org Referral & Care Coordination (Track 1)
> **Project:** Oflex
> **Purpose of this document:** Required submission artifact per the BuildersVault submission checklist. Explains how Oflex respects the constraints for Track 1.

## The four non-negotiable Track 1 constraints, and how we honor them

The starter kit calls out four privacy and consent constraints for Track 1. Oflex enforces all four in pure, deterministic, unit-tested Python — never via the AI layer. Every constraint is covered by passing tests in `tests/test_privacy_gates.py`.

### 1. OCAP-protected records

**Constraint:** First Nations / Métis / Inuit clients whose records are OCAP-protected cannot be shared across organizations without Nation-level authorization.

**How Oflex enforces it:**
- The `can_share_record(client, viewing_org_id)` gate blocks any cross-org view of an OCAP-protected record unless the viewer is the client's primary org.
- The `can_display_duplicate_match()` gate refuses to show OCAP-protected matches to a new applicant during duplicate detection, even when the new applicant's consent scope is broad. The match is routed to a coordinator with proper authorization instead.
- The intake flow asks Indigenous applicants whether they want OCAP protection, with a plain-language explanation and a default-conservative posture.

**Tests:** `test_ocap_protected_blocks_cross_org_view`, `test_ocap_protected_allows_primary_org_view`, `test_ocap_existing_record_blocks_display_even_with_broad_consent`.

### 2. Withdrawn and expired consents

**Constraint:** Consent records that have been withdrawn, expired, or superseded must not be acted on.

**How Oflex enforces it:**
- The `can_use_consent(consent)` gate returns false for any consent whose `status != 'active'`, whose `expiry_date` is in the past, or whose `withdrawal_date` is set.

**Tests:** `test_withdrawn_consent_rejected`, `test_expired_consent_rejected`, `test_active_consent_with_purpose_codes_usable`.

### 3. FOIPPA purpose-code requirement

**Constraint:** Under FOIPPA's statutory information-sharing rules, every consent record must specify the purpose for which information may be used. Records with empty purpose codes cannot be relied on for sharing.

**How Oflex enforces it:**
- `can_use_consent()` rejects consents with empty `purpose_codes`.
- `validate_consent_before_save()` refuses to persist a new consent record without `purpose_codes`.
- The consent UI in `app/pages/consent.py` requires the applicant to pick at least one purpose before the "Save my privacy choices" button activates.

**Tests:** `test_consent_without_purpose_codes_rejected`, `test_new_consent_without_purpose_codes_rejected`.

### 4. Sharing scope at display time

**Constraint:** A consent record's `sharing_scope_type` of `org` (single-agency) or `none` (no sharing) must prevent any cross-agency join or display.

**How Oflex enforces it:**
- The `can_display_duplicate_match()` gate returns `False` for new consents scoped `org` or `none`. No cross-agency match is surfaced — the user sees a generic "no matches found in your scope" message instead.
- The consent UI shows applicants what each scope means in plain language before they pick.

**Tests:** `test_org_scope_blocks_duplicate_display`, `test_none_scope_blocks_duplicate_display`, `test_ca_table_scope_allows_non_ocap_match`.

## Where AI is and is not used

Oflex uses Anthropic's Claude API for three things:

1. **Translation:** mapping plain-English answers (e.g., "I crashed at my sister's place") to HIFIS schema enum values (`current_sleeping_location: couch`).
2. **Summarization:** generating a plain-language review summary of an intake record.
3. **Scoped help assistant:** answering applicant questions about Oflex and the application.

**No privacy decision is delegated to the AI.** The four constraints above are enforced by deterministic Python functions that judges can read in `app/privacy_gates.py` and run as tests. If the AI is unavailable or returns an unexpected answer, the privacy gates still hold.

## Help assistant scope and crisis routing

The in-app help assistant (`app/help_chat.py`, `app/ai_layer.HELP_SYSTEM`) is constrained by a strict system prompt:

- **In scope:** how to use Oflex, what the Income Assistance application asks for, what to do when missing common documents (no SIN, no fixed address, no ID), BCeID/MySelfServe basics, where to call for in-person help.
- **Out of scope:** life advice, medical or symptom questions, legal advice, political or religious topics, general knowledge, anything unrelated to applying for Income Assistance. The assistant declines and redirects to an appropriate resource (e.g., 811 for health, 211 for general services).
- **Crisis handling:** if the user expresses intent to harm themselves or others, or describes an emergency, the assistant routes them to **9-8-8** (Canada's mental health crisis line, free 24/7) and **911**, and pauses the application conversation.

## What we explicitly do not do

- We do not use any real PII. All data shipped in `data/` is synthetic (CC BY 4.0 from the starter kit).
- We do not submit anything to the BC government on the applicant's behalf. Oflex produces a takeaway PDF; the applicant chooses what to do with it.
- We do not auto-create email accounts. The Proton Mail walkthrough is instructional only — the user clicks the buttons themselves.
- We do not store data anywhere that persists between sessions. The applicant's inputs live in Streamlit session state for the duration of the session, then are gone.

## Auditability

Every privacy gate is in `app/privacy_gates.py`, ~150 lines, no AI dependencies. Judges can read it end-to-end in five minutes and run the tests with `pytest tests/ -v`.
