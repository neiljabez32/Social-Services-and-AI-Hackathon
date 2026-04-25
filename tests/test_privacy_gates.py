"""
Tests that prove the privacy gates and duplicate detector work.

Run with:
    pytest tests/

Per the kit's submission checklist, these prove that our privacy gates
actually reject bad inputs. Judges can run them.
"""

import pandas as pd
import pytest

from app.schema import ClientRecord, ConsentRecord
from app.privacy_gates import (
    can_share_record,
    can_use_consent,
    can_display_duplicate_match,
    validate_consent_before_save,
)
from app.duplicate_detector import find_potential_duplicates, name_similarity, soundex


# -----------------------------------------------------------------------------
# Privacy gate: OCAP protection
# -----------------------------------------------------------------------------


def test_ocap_protected_blocks_cross_org_view():
    client = {
        "ocap_protected": True,
        "primary_org_id": "ORG-0001",
    }
    allowed, reason = can_share_record(client, viewing_org_id="ORG-0003")
    assert not allowed
    assert "OCAP" in reason


def test_ocap_protected_allows_primary_org_view():
    client = {
        "ocap_protected": True,
        "primary_org_id": "ORG-0001",
    }
    allowed, _ = can_share_record(client, viewing_org_id="ORG-0001")
    assert allowed


def test_non_ocap_record_freely_visible():
    client = {"ocap_protected": False, "primary_org_id": "ORG-0001"}
    allowed, _ = can_share_record(client, viewing_org_id="ORG-0005")
    assert allowed


# -----------------------------------------------------------------------------
# Privacy gate: consent usability
# -----------------------------------------------------------------------------


def test_active_consent_with_purpose_codes_usable():
    consent = {
        "status": "active",
        "expiry_date": "2099-01-01",
        "withdrawal_date": None,
        "purpose_codes": "case_mgmt",
    }
    ok, _ = can_use_consent(consent)
    assert ok


def test_withdrawn_consent_rejected():
    consent = {
        "status": "withdrawn",
        "withdrawal_date": "2025-01-01",
        "purpose_codes": "case_mgmt",
    }
    ok, reason = can_use_consent(consent)
    assert not ok


def test_expired_consent_rejected():
    consent = {
        "status": "expired",
        "expiry_date": "2020-01-01",
        "purpose_codes": "case_mgmt",
    }
    ok, _ = can_use_consent(consent)
    assert not ok


def test_consent_without_purpose_codes_rejected():
    """FOIPPA constraint — kit non-negotiable #3."""
    consent = {
        "status": "active",
        "expiry_date": "2099-01-01",
        "purpose_codes": "",
    }
    ok, reason = can_use_consent(consent)
    assert not ok
    assert "purpose" in reason.lower()


# -----------------------------------------------------------------------------
# Privacy gate: duplicate match display
# -----------------------------------------------------------------------------


def test_org_scope_blocks_duplicate_display():
    """Kit non-negotiable #4 — single_agency scope must not expose cross-agency joins."""
    existing = {"ocap_protected": False}
    new_client = ClientRecord(first_name="Jane", last_name="Doe")
    consent = ConsentRecord(sharing_scope_type="org")
    allowed, reason = can_display_duplicate_match(existing, new_client, consent)
    assert not allowed
    assert "org" in reason


def test_none_scope_blocks_duplicate_display():
    existing = {"ocap_protected": False}
    new_client = ClientRecord()
    consent = ConsentRecord(sharing_scope_type="none")
    allowed, _ = can_display_duplicate_match(existing, new_client, consent)
    assert not allowed


def test_ocap_existing_record_blocks_display_even_with_broad_consent():
    existing = {"ocap_protected": True}
    new_client = ClientRecord()
    consent = ConsentRecord(sharing_scope_type="ca_table")
    allowed, reason = can_display_duplicate_match(existing, new_client, consent)
    assert not allowed
    assert "OCAP" in reason or "authorization" in reason.lower()


def test_ca_table_scope_allows_non_ocap_match():
    existing = {"ocap_protected": False}
    new_client = ClientRecord()
    consent = ConsentRecord(sharing_scope_type="ca_table")
    allowed, _ = can_display_duplicate_match(existing, new_client, consent)
    assert allowed


# -----------------------------------------------------------------------------
# New consent validation before save
# -----------------------------------------------------------------------------


def test_new_consent_without_purpose_codes_rejected():
    consent = ConsentRecord(
        client_id="CLI-X",
        collecting_org_id="ORG-MSD",
        purpose_codes="",
        status="active",
    )
    errors = validate_consent_before_save(consent)
    assert any("purpose_codes" in e for e in errors)


def test_named_agencies_scope_requires_agency_list():
    consent = ConsentRecord(
        client_id="CLI-X",
        collecting_org_id="ORG-MSD",
        purpose_codes="case_mgmt",
        status="active",
        sharing_scope_type="named_agencies",
        sharing_scope_agency_ids=None,
    )
    errors = validate_consent_before_save(consent)
    assert any("agency" in e.lower() for e in errors)


def test_valid_consent_passes():
    consent = ConsentRecord(
        client_id="CLI-X",
        collecting_org_id="ORG-MSD",
        purpose_codes="case_mgmt;referral",
        status="active",
        sharing_scope_type="cluster",
    )
    assert validate_consent_before_save(consent) == []


# -----------------------------------------------------------------------------
# Duplicate detection basics
# -----------------------------------------------------------------------------


def test_name_similarity_exact_match():
    assert name_similarity("Jane", "Jane") == 1.0


def test_name_similarity_handles_casing():
    assert name_similarity("Jane", "jane") == 1.0


def test_name_similarity_handles_empty():
    assert name_similarity("", "Jane") == 0.0
    assert name_similarity(None, "Jane") == 0.0


def test_soundex_matches_phonetic_variants():
    # Smith and Smyth should share a Soundex code
    assert soundex("Smith") == soundex("Smyth")


def test_duplicate_detector_finds_obvious_match():
    existing = pd.DataFrame([
        {
            "client_id": "CLI-0001",
            "first_name": "Jane",
            "last_name": "Doe",
            "dob": "1990-01-15",
            "aliases": None,
            "ocap_protected": False,
            "primary_org_id": "ORG-0001",
        }
    ])
    new = ClientRecord(first_name="Jane", last_name="Doe", dob="1990-01-15")
    matches = find_potential_duplicates(new, existing, threshold=0.5)
    assert len(matches) == 1
    assert matches[0][0] > 0.8  # high score


def test_duplicate_detector_rejects_different_person():
    existing = pd.DataFrame([
        {
            "client_id": "CLI-0001",
            "first_name": "Alice",
            "last_name": "Smith",
            "dob": "1970-01-01",
            "aliases": None,
            "ocap_protected": False,
            "primary_org_id": "ORG-0001",
        }
    ])
    new = ClientRecord(first_name="Bob", last_name="Jones", dob="2000-12-25")
    matches = find_potential_duplicates(new, existing, threshold=0.55)
    assert len(matches) == 0


# -----------------------------------------------------------------------------
# PDF generation smoke test
# -----------------------------------------------------------------------------


def test_pdf_summary_generates_valid_bytes():
    """The PDF generator should produce real PDF bytes from a complete record."""
    from app.pdf_summary import build_summary_pdf

    client = ClientRecord(
        client_id="CLI-NEW-TEST",
        first_name="Jane",
        last_name="Doe",
        dob="1990-01-15",
        age=35,
        current_sleeping_location="couch",
        housing_status="homeless",
        indigenous_identity="none",
        phone="250-555-0100",
        email="jane.doe@proton.me",
    )
    consent = ConsentRecord(
        consent_id="CNS-NEW-TEST",
        client_id="CLI-NEW-TEST",
        collecting_org_id="ORG-MSD",
        purpose_codes="case_mgmt;referral",
        data_categories="demographics;medical",
        sharing_scope_type="cluster",
        given_date="2026-04-25",
        expiry_date="2027-04-25",
    )
    pdf_bytes = build_summary_pdf(client, consent)

    # Real PDFs start with the magic bytes %PDF-
    assert pdf_bytes[:5] == b"%PDF-"
    # And should be more than a few hundred bytes
    assert len(pdf_bytes) > 1000


def test_pdf_summary_handles_minimal_record():
    """PDF generator must not crash when most fields are empty."""
    from app.pdf_summary import build_summary_pdf

    client = ClientRecord(first_name="X", last_name="Y")
    consent = ConsentRecord(
        consent_id="CNS-MIN",
        client_id="CLI-MIN",
        collecting_org_id="ORG-MSD",
        purpose_codes="case_mgmt",
        sharing_scope_type="org",
        given_date="2026-04-25",
    )
    pdf_bytes = build_summary_pdf(client, consent)
    assert pdf_bytes[:5] == b"%PDF-"
