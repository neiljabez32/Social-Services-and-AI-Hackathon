"""
HIFIS-aligned schema definitions for Track 1.

These mirror the starter kit's `clients` and `consent_records` tables exactly,
so anything we create here can be appended directly into the kit's data model.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# -----------------------------------------------------------------------------
# Enumerations (verbatim from dictionary/fields.csv)
# -----------------------------------------------------------------------------

GENDER_VALUES = ["man", "woman", "non-binary", "trans", "other", "unknown"]

INDIGENOUS_IDENTITY_VALUES = ["first_nations", "metis", "inuit", "none", "declined"]

CITIZENSHIP_VALUES = ["citizen", "pr", "refugee", "claimant", "other", "unknown"]

SLEEPING_LOCATION_VALUES = [
    "shelter",
    "unsheltered",
    "couch",
    "supportive",
    "institution",
    "housed",
]

HOUSING_STATUS_VALUES = [
    "homeless",
    "at_risk",
    "provisionally_housed",
    "housed",
    "unknown",
]

CONSENT_TYPE_VALUES = ["implied", "explicit", "substitute", "emergency"]

CONSENT_STATUS_VALUES = [
    "active",
    "expired",
    "withdrawn",
    "superseded",
    "pending",
]

LEGAL_BASIS_VALUES = [
    "consent",
    "public_body",
    "legal_obligation",
    "vital_interest",
]

SHARING_SCOPE_VALUES = [
    "none",
    "org",
    "cluster",
    "ca_table",
    "named_agencies",
]

CONSENT_SOURCE_VALUES = ["paper", "verbal", "digital_signature", "kiosk"]

PURPOSE_CODES = [
    "case_mgmt",
    "coordinated_access",
    "reporting",
    "referral",
    "safety_planning",
]

DATA_CATEGORIES = [
    "demographics",
    "medical",
    "mental_health",
    "substance_use",
    "financial",
    "family",
    "contact",
]

# Governing nations in the Victoria area (per starter kit overview.md)
GOVERNING_NATIONS = [
    "Songhees Nation",
    "Esquimalt Nation",
    "Tsawout First Nation",
    "Pauquachin First Nation",
    "Other / Not listed",
]


# -----------------------------------------------------------------------------
# Dataclasses matching the kit's schema
# -----------------------------------------------------------------------------


@dataclass
class ClientRecord:
    """Mirrors `clients` table from the starter kit."""

    client_id: str = ""
    primary_org_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    middle_name: Optional[str] = None
    aliases: Optional[str] = None  # semi-colon separated
    dob: Optional[str] = None  # ISO date string or None
    age: Optional[int] = None
    gender: Optional[str] = None
    indigenous_identity: Optional[str] = None
    citizenship_status: Optional[str] = None
    veteran_status: Optional[bool] = None
    primary_language: Optional[str] = "english"
    current_sleeping_location: Optional[str] = None
    housing_status: Optional[str] = None
    ocap_protected: bool = False
    ocap_governing_nation: Optional[str] = None
    ocap_data_use_conditions: Optional[str] = None
    consent_coverage_level: Optional[str] = None
    default_sharing_scope: Optional[str] = None
    current_consent_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


@dataclass
class ConsentRecord:
    """Mirrors `consent_records` table from the starter kit."""

    consent_id: str = ""
    client_id: str = ""
    collecting_org_id: str = ""
    dsa_id: Optional[int] = None
    consent_type: str = "explicit"
    status: str = "active"
    legal_basis: str = "consent"
    purpose_codes: str = ""  # semi-colon separated, must not be empty for FOIPPA
    data_categories: str = ""
    sharing_scope_type: str = "org"
    sharing_scope_agency_ids: Optional[str] = None
    given_date: str = ""
    effective_date: str = ""
    expiry_date: Optional[str] = None
    withdrawal_date: Optional[str] = None
    superseded_date: Optional[str] = None
    consent_source: str = "digital_signature"
    obtained_by_user_id: Optional[str] = None
    witness_user_id: Optional[str] = None
    consent_document_ref: Optional[str] = None
    notes: Optional[str] = None


# -----------------------------------------------------------------------------
# Plain-language mappings (for the AI layer to translate)
# -----------------------------------------------------------------------------

SLEEPING_LOCATION_PLAIN = {
    "I slept at a shelter": "shelter",
    "I slept outside (a park, doorway, tent, vehicle)": "unsheltered",
    "I stayed on a friend's or family member's couch": "couch",
    "I stayed in supportive or transitional housing": "supportive",
    "I stayed in a hospital, jail, or treatment centre": "institution",
    "I stayed in my own home or a place I rent": "housed",
}

SHARING_SCOPE_PLAIN = {
    "Just this agency — no one else": "org",
    "Agencies I've worked with before that have a sharing agreement": "cluster",
    "Any agency that's helping me coordinate housing or support": "ca_table",
    "Only specific agencies I name": "named_agencies",
    "I don't want my information shared with anyone": "none",
}

INDIGENOUS_PLAIN = {
    "First Nations": "first_nations",
    "Métis": "metis",
    "Inuit": "inuit",
    "No, I don't identify as Indigenous": "none",
    "I'd rather not say": "declined",
}
