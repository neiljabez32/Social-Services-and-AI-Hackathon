"""
Duplicate client detection.

Baseline approach per the kit's README:
  Soundex blocking + string similarity + DOB match + alias check.

The kit says this hits ~60-70% recall at 80% precision. For our demo the value
is not in beating the baseline — it's in wiring it into the consent-aware
display layer. If we have time Friday we can swap in Splink.
"""

from difflib import SequenceMatcher
import pandas as pd
import jellyfish


def soundex(name: str) -> str:
    if not name or pd.isna(name):
        return ""
    try:
        return jellyfish.soundex(str(name))
    except Exception:
        return ""


def name_similarity(a: str, b: str) -> float:
    if not a or not b or pd.isna(a) or pd.isna(b):
        return 0.0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()


def dob_match(a: str, b: str) -> float:
    """Returns 1.0 for exact match, 0.5 for year-only match, 0 otherwise."""
    if not a or not b or pd.isna(a) or pd.isna(b):
        return 0.0
    try:
        da = pd.to_datetime(a)
        db = pd.to_datetime(b)
        if da == db:
            return 1.0
        if da.year == db.year:
            return 0.5
        return 0.0
    except Exception:
        return 0.0


def alias_hit(alias_field: str, first_name: str, last_name: str) -> float:
    """Check if new intake's name appears in an existing client's aliases."""
    if not alias_field or pd.isna(alias_field):
        return 0.0
    aliases = str(alias_field).lower().split(";")
    target = f"{first_name} {last_name}".lower().strip()
    for a in aliases:
        if name_similarity(a.strip(), target) > 0.85:
            return 1.0
    return 0.0


def match_score(new_client, existing_row) -> tuple[float, list[str]]:
    """
    Compute a match score between a new client record and an existing client row.

    Returns (score in [0,1], list of feature descriptions that fired).
    """
    reasons = []
    score = 0.0

    fn_sim = name_similarity(new_client.first_name, existing_row.get("first_name", ""))
    ln_sim = name_similarity(new_client.last_name, existing_row.get("last_name", ""))
    name_score = (fn_sim + ln_sim) / 2
    if name_score >= 0.85:
        reasons.append(f"Name similarity high ({name_score:.2f})")
        score += 0.45 * name_score
    elif name_score >= 0.6:
        reasons.append(f"Name similarity moderate ({name_score:.2f})")
        score += 0.25 * name_score

    # Soundex blocking — cheap phonetic match
    if new_client.last_name and existing_row.get("last_name"):
        if soundex(new_client.last_name) == soundex(existing_row.get("last_name", "")):
            reasons.append("Last-name Soundex match")
            score += 0.15

    # DOB
    dob_result = dob_match(new_client.dob, existing_row.get("dob", ""))
    if dob_result == 1.0:
        reasons.append("Date of birth exact match")
        score += 0.35
    elif dob_result == 0.5:
        reasons.append("Birth year match (day/month differ)")
        score += 0.1

    # Alias hit
    alias_result = alias_hit(
        existing_row.get("aliases", ""), new_client.first_name, new_client.last_name
    )
    if alias_result > 0:
        reasons.append("New name matches one of existing client's aliases")
        score += 0.15

    # Clamp
    score = min(score, 1.0)
    return score, reasons


def find_potential_duplicates(
    new_client, existing_clients_df: pd.DataFrame, threshold: float = 0.55
):
    """
    Search the full existing client table for potential matches.
    Returns a list of (score, reasons, row) tuples, sorted desc by score.
    """
    if not new_client.last_name:
        return []

    # Cheap blocking: only compare rows sharing last-name Soundex
    target_soundex = soundex(new_client.last_name)
    if target_soundex:
        blocked = existing_clients_df[
            existing_clients_df["last_name"]
            .astype(str)
            .apply(lambda x: soundex(x) == target_soundex)
        ]
    else:
        blocked = existing_clients_df

    results = []
    for _, row in blocked.iterrows():
        score, reasons = match_score(new_client, row)
        if score >= threshold:
            results.append((score, reasons, row))

    results.sort(key=lambda t: t[0], reverse=True)
    return results
