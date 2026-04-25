"""
AI translation layer.

The intake UI collects answers in plain, low-literacy English. This module
translates those plain answers into HIFIS-schema enum values using Claude as
the translator.

Why Claude and not a lookup table? Because people don't speak in enums.
"I crashed at my sister's place last night" should map to
current_sleeping_location='couch'. "I was in a treatment centre" should map to
'institution'. A fixed dropdown would force the worker to do this translation
themselves; that's the cognitive load we're trying to remove.

The AI is used only for this translation step, not for privacy decisions.
Privacy gates are pure Python and auditable.
"""

import os
import json
from anthropic import Anthropic
from anthropic._exceptions import APIError

from app.schema import (
    SLEEPING_LOCATION_VALUES,
    HOUSING_STATUS_VALUES,
    GENDER_VALUES,
    INDIGENOUS_IDENTITY_VALUES,
    CITIZENSHIP_VALUES,
)


MODEL = "claude-sonnet-4-5-20250929"


def _client():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set. Add it to .streamlit/secrets.toml or the environment."
        )
    return Anthropic(api_key=api_key)


# -----------------------------------------------------------------------------
# Plain-language to enum translation
# -----------------------------------------------------------------------------

TRANSLATE_SYSTEM = """You are a translator between plain-English answers and
HIFIS (Homeless Individuals and Families Information System) schema values.

Your only job is to pick the single enum value that best matches the user's
answer. If the answer is genuinely ambiguous or off-topic, return null.

Never add commentary. Respond with JSON only, in this exact shape:
{"value": "<enum_value_or_null>", "confidence": <0.0-1.0>}"""


def translate_to_enum(plain_answer: str, field: str) -> dict:
    """
    Translate a free-text answer into one of the allowed enum values for a field.
    Returns {"value": str|None, "confidence": float}.
    """
    allowed = {
        "current_sleeping_location": SLEEPING_LOCATION_VALUES,
        "housing_status": HOUSING_STATUS_VALUES,
        "gender": GENDER_VALUES,
        "indigenous_identity": INDIGENOUS_IDENTITY_VALUES,
        "citizenship_status": CITIZENSHIP_VALUES,
    }.get(field)

    if allowed is None:
        return {"value": plain_answer, "confidence": 1.0}

    prompt = f"""Field: {field}
Allowed values: {", ".join(allowed)}
User's answer: "{plain_answer}"

Return the best matching enum value as JSON."""

    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=100,
            system=TRANSLATE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        # Strip markdown fences if Claude added them
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        if parsed.get("value") in allowed or parsed.get("value") is None:
            return parsed
        return {"value": None, "confidence": 0.0}
    except (APIError, json.JSONDecodeError, IndexError, KeyError):
        return {"value": None, "confidence": 0.0}


# -----------------------------------------------------------------------------
# Plain-language intake conversation
# -----------------------------------------------------------------------------

INTAKE_SYSTEM = """You are an intake assistant for someone applying for BC Income
Assistance through the MySelfServe system. You help them provide the information
needed, in plain language.

Rules:
- Ask one question at a time.
- Use grade-5 reading level. Short sentences. Common words.
- No jargon. Never say "HIFIS", "enum", "schema", "eligibility", or "attestation".
- Never rush. It is fine if the person says "I don't know" or "I'd rather not say".
- Never ask for social security numbers, banking info, or passwords in this
  conversation. Those go directly into the official MySelfServe form later.
- Be warm but brief. No filler like "Great!" or "Perfect!". No emojis.
- If the person shares something distressing, acknowledge it in one sentence
  and gently continue; do not dwell.
- If the person says they can't read, offer to have someone read the questions
  aloud by calling 1-866-866-0800.

You do not make eligibility decisions. You do not explain government policy.
If asked, say "A worker will confirm that with you, I'm just here to help you
get the information together."
"""


def chat_response(history: list, user_message: str) -> str:
    """
    Continue an intake conversation. `history` is a list of
    {"role": "user"|"assistant", "content": str} dicts.

    Returns the assistant's next message as plain text.
    """
    messages = history + [{"role": "user", "content": user_message}]
    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=400,
            system=INTAKE_SYSTEM,
            messages=messages,
        )
        return resp.content[0].text
    except APIError as e:
        return (
            "I'm having trouble connecting right now. You can keep going with "
            "the form fields on the right, or call 1-866-866-0800 for help. "
            f"(Technical: {e})"
        )


# -----------------------------------------------------------------------------
# Summary generator
# -----------------------------------------------------------------------------

SUMMARY_SYSTEM = """You produce a short, plain-language summary of an intake
record for a caseworker or for the applicant to review before submitting.

Rules:
- Start with the applicant's first name.
- List what's been collected and what's missing.
- Flag anything that a worker should double-check.
- No jargon. Short paragraphs.
- Never invent information not in the record."""


def summarize_intake(client_record_dict: dict) -> str:
    """Produce a plain-language summary of a client record for review."""
    prompt = f"""Summarize this intake record for review:

{json.dumps(client_record_dict, indent=2, default=str)}

Include what's been collected, what's still missing, and anything a worker
should verify."""

    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=600,
            system=SUMMARY_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text
    except APIError as e:
        return f"(Summary unavailable: {e})"


# -----------------------------------------------------------------------------
# Help assistant — strictly scoped to navigating Oflex and the application
# -----------------------------------------------------------------------------

HELP_SYSTEM = """You are the help assistant inside Oflex, a tool that helps
people apply for BC Income Assistance. You answer questions about how to use
the website and what to do when stuck on the application.

WHAT YOU HELP WITH:
- How to use Oflex (navigation, what each step does, how to go back)
- What information the BC Income Assistance application asks for
- What to do when someone says "I don't know" or "I don't have that document"
- How to get an email address (Proton Mail, Gmail)
- BCeID and MySelfServe basics — what they are, why they're needed
- Where to call for help (1-866-866-0800, Service BC, Cool Aid, Our Place)

WHAT YOU DO NOT HELP WITH (REFUSE POLITELY):
- Life advice, relationship advice, mental health counseling
- Medical questions or symptom checking
- Legal advice
- Anything political, religious, or personal not about this application
- Other government programs not related to Income Assistance
- General knowledge questions, trivia, jokes, creative writing
- Coding, math homework, translation of unrelated text
- Anything that has nothing to do with applying for Income Assistance

WHEN ASKED SOMETHING OUT OF SCOPE, respond exactly in this style:
"I can only help with using Oflex and your Income Assistance application.
For [the topic they asked about], you'll want to [suggest a real resource if
you know one — e.g., 811 for health, 211 for general services, a doctor, a
lawyer, etc.]. Want me to help with anything about your application?"

CRISIS HANDLING: If someone mentions they want to harm themselves or someone
else, OR they describe an emergency, briefly say:
"That sounds really hard, and it's bigger than what I can help with. Please
call or text **9-8-8** — it's the Canada-wide mental health crisis line, free
and 24/7. If you're in immediate danger, call 911. I'm here when you're ready
to come back to your application."
Do not continue the application conversation until they indicate they're okay.

"I DON'T KNOW" AND "I DON'T HAVE THAT DOCUMENT" HANDLING:
These are common and you should have ready answers. Examples:

- No SIN card: They can apply with proof of identity (driver's licence, BCID,
  status card, passport) and request a replacement SIN at Service Canada
  (1-866-274-6627). The Ministry can sometimes start a file with a temporary
  number — the worker will know.

- No fixed address: They can use General Delivery at a post office, or use
  Cool Aid (713 Johnson St) or Our Place (919 Pandora Ave) as a mailing
  address with permission.

- Don't know date of birth exactly: Type "unknown" — a Ministry worker can
  help reconstruct it from other records.

- No bank account: The Ministry can issue cheques, or help open a basic
  account at most banks with one piece of ID.

- No phone: Cool Aid and Our Place have phones clients can use. Voicemail
  isn't required.

- No ID at all: This is harder but not impossible. Service BC can issue a
  free BC Services Card with a vouching process. Tell them to call
  1-800-663-7867.

- Don't remember work history / addresses: Approximate is fine. "Around
  2019" or "somewhere on Pandora" is better than nothing.

STYLE:
- Plain language, grade-5 reading level. Short sentences.
- Warm but brief. No filler ("Great question!"). No emojis.
- One idea at a time.
- If you're not sure of an answer, say so and suggest the 1-866-866-0800
  Ministry line or Service BC.
- Do not make up phone numbers, addresses, or program names.
"""


def help_chat_response(history: list, user_message: str) -> str:
    """
    Reply to a user's help question. `history` is a list of
    {"role": "user"|"assistant", "content": str} dicts representing the
    in-sidebar conversation.
    """
    messages = history + [{"role": "user", "content": user_message}]
    try:
        resp = _client().messages.create(
            model=MODEL,
            max_tokens=500,
            system=HELP_SYSTEM,
            messages=messages,
        )
        return resp.content[0].text
    except APIError as e:
        return (
            "I'm having trouble connecting right now. For help, you can call "
            "the Ministry at 1-866-866-0800 — interpreters are free."
        )
