# Devpost Submission Copy

> Paste these into the matching Devpost fields when submitting. Edit the team names and any links.

---

## Project name
**Oflex**

## Tagline (one sentence, ≤ 200 chars)
A plain-language, low-literacy front door to BC Income Assistance — guided intake, consent-aware duplicate detection, and a printable PDF the applicant takes to a Ministry worker.

## Track
Inter-Org Referral & Care Coordination (Track 1)

## Team
_[your names — edit before submitting]_

## "Inspiration" section
During hackathon week we visited three Victoria social services orgs. The Ministry of Social Development told us their #1 onboarding bottleneck for new Income Assistance applicants is computer literacy — BCeID, email, PIN, and the application form together overwhelm many of the people who need help most. The Ministry refers people to Cool Aid or Our Place to get help filling things out, but those orgs are stretched thin. New applicants can wait weeks. Oflex is what the Ministry can refer them to instead — a guided, plain-language intake that respects their privacy, captures consent properly, and produces something they can take to a worker on Monday morning.

## "What it does" section
Oflex walks an applicant — on their own or with a worker — through the information needed to apply for BC Income Assistance. One question at a time, grade-five reading level, in their own words. A built-in AI help assistant answers questions about missing documents (no SIN, no address, no ID) and refuses anything off-topic. The applicant picks their privacy scope in plain language, which Oflex maps to a schema-valid consent record. On save, Oflex runs consent-aware duplicate detection against the existing 800-client coordination dataset — surfacing matches only when consent and OCAP permit, and failing safe otherwise. The applicant leaves with a printable PDF summary.

## "How we built it" section
- **Streamlit** for the UI — chosen because it matches the starter kit's own scaffold and judges find it familiar.
- **Anthropic Claude API** for plain-English-to-schema translation, summary generation, and the scoped help assistant.
- **HIFIS-aligned dataclasses** that map directly to the starter kit's `clients` and `consent_records` schema.
- **Pure-Python privacy gates** (`app/privacy_gates.py`) enforcing all four Track 1 non-negotiables — OCAP, withdrawn/expired consent, FOIPPA purpose codes, sharing-scope display rules. No privacy decision is delegated to the AI.
- **Soundex + sequence matching baseline** for entity resolution, with a consent-aware display layer on top.
- **ReportLab** for the printable PDF takeaway.
- **22 passing tests** covering every privacy gate.

## "Challenges we ran into"
The Ministry interview surfaced a problem upstream of what Track 1 is designed for. We had to figure out how to honor a real stakeholder pain (onboarding) while still working with the kit's data model (coordination). We landed on positioning Oflex as the front door of the kit's system — every intake produces a schema-valid record. We also had to think carefully about what AI should and should not be trusted with. Privacy decisions had to be deterministic and auditable, so those gates are pure Python. AI is used only for translation, summary, and scoped help.

## "Accomplishments we're proud of"
- All four Track 1 non-negotiables enforced and unit-tested. 22 passing tests.
- A help assistant that has a strict scope and crisis-routes to 9-8-8 — not a generic chatbot bolted on.
- The duplicate detection demo lands either way: with broad consent it shows the match; with narrow consent it fails safe. Same data, different outcomes, by design.
- A printable PDF that a real Ministry worker could actually use Monday morning.

## "What we learned"
The four Track 1 constraints from the kit aren't abstract — they map directly to PIPA, FOIPPA, and OCAP. Building privacy gates is mostly a discipline problem, not a complexity problem. Plain language is hard; we rewrote almost every UI string at least twice.

## "What's next for Oflex"
- Replace the baseline duplicate detector with **Splink** (proper Bayesian ER).
- Add a worker review queue for Ministry staff.
- Voice input mode for low-literacy clients.
- In-app translation for the top 5 languages spoken in Victoria's unhoused community.

## Built with
streamlit, anthropic-claude, python, reportlab, jellyfish, pandas, pytest

## Privacy & Safety statement (for the form field, abbreviated)
Oflex enforces all four Track 1 non-negotiables — OCAP cross-org blocking, withdrawn/expired consent rejection, FOIPPA purpose-code requirement, and sharing-scope-at-display — in pure, unit-tested Python. The AI is used for translation, summarization, and a scoped help assistant only; no privacy decision is delegated to the AI. The help assistant refuses life advice and routes any mention of self-harm to 9-8-8. Full statement in `PRIVACY.md` in the repo.

## Repo URL
_[paste your GitHub URL]_

## Demo video URL
_[paste your YouTube/Loom URL]_

## Try it out links
- Live: _[Streamlit Cloud URL if deployed]_
- Source: _[GitHub URL]_
