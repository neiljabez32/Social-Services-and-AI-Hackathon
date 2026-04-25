Oflex
> **A plain-language, low-literacy front door to BC Income Assistance.**
> Built for the BuildersVault Social Services Hackathon — April 25, 2026.
Track: Inter-Org Referral & Care Coordination (Track 1)
Team: [your names here — edit before submitting]
Live demo: [Streamlit Cloud URL if hosted, otherwise "see screen recording below"]
Screen recording: [YouTube/Loom link]
---
What we built
Oflex is a guided intake tool a person can use, on their own or with a worker, to gather everything they need to apply for BC Income Assistance through the Ministry of Social Development's MySelfServe system.
It does three things:
Walks the applicant through plain-language questions — one at a time, grade-five reading level, in their own words. A built-in AI help assistant answers questions about missing documents (no SIN, no address, no ID), and refuses anything off-topic.
Records a properly-scoped consent decision that maps to the starter kit's `consent_records` schema — sharing scope, purpose codes, data categories, OCAP protection, all chosen by the applicant in language they understand.
Runs consent-aware duplicate detection against the existing 800-client coordination dataset. If a match exists but the applicant's consent (or the existing record's OCAP status) doesn't permit displaying it, Oflex fails safe and routes the case to a coordinator with proper authorization.
The applicant leaves with a printable PDF summary they can take to a Ministry worker, or use to fill out the official MySelfServe form.
---
Why this problem
During hackathon week, our team met with three Victoria social services organizations:
Ministry of Social Development (MySelfServe team) told us their #1 onboarding bottleneck is computer literacy. New applicants struggle with BCeID + email + PIN + form completion. The Ministry refers them to Cool Aid or Our Place for help — but those agencies are stretched thin, so the process can take weeks.
Cool Aid Health Centre told us new patient intake is also slowed by referrals fragmented across multiple databases.
Our Place Society told us their intake is short by design — name, history, three pages — but they often see the same person who's already been intook elsewhere.
All three problems share a root cause: fragmented intake, with no consistent way to capture consent or detect duplicates. Oflex sits at the front door of the Track 1 coordination system and fixes that for new applicants, while leaving every existing record untouched.
---
How it fits Track 1
Track 1 is about coordination across the 9+ social services orgs in Victoria. The starter kit's data model captures clients, consent, referrals, and service encounters. Oflex slots in at the intake point:
Every new intake produces a schema-valid `clients` record (HIFIS-aligned).
Every record is paired with a first-class `consent_records` entry with non-empty `purpose_codes`, an explicit `sharing_scope_type`, and OCAP awareness.
Cross-agency duplicate detection runs on save, gated by all four of the kit's non-negotiable privacy constraints.
Judges who picked Track 1 because of the consent and OCAP framing will find Oflex enforces those constraints in pure, tested Python — never in the AI layer.
---
Privacy & safety statement
Oflex treats the four non-negotiable Track 1 constraints as first-class rules, enforced in pure Python and covered by tests in `tests/test_privacy_gates.py` (22 passing):
OCAP-protected records are blocked from cross-org view unless the viewer is the primary org. Our duplicate-display gate also refuses to surface OCAP-protected matches even when the new applicant's consent is broad. (`can_share_record`, `can_display_duplicate_match`)
Withdrawn and expired consents are rejected before any downstream use. (`can_use_consent`)
FOIPPA's purpose-code requirement is enforced at save time. A consent record without `purpose_codes` cannot be persisted. (`validate_consent_before_save`)
Sharing scope `org` or `none` blocks cross-agency joins at display time, including the duplicate-detection demo itself.
The AI is used only to translate plain-English answers into schema enums and to generate plain-language summaries. No privacy decision is delegated to the AI. Every gate is deterministic, auditable, and unit-tested.
The built-in help assistant has a strictly scoped system prompt: it answers questions about Oflex and the application, refuses off-topic and life-advice questions, and routes any mention of self-harm or crisis to 9-8-8 (Canada's mental health crisis line) and 911.
---
Run it locally
Requires Python 3.10+.
```bash
git clone https://github.com/<your-username>/oflex.git
cd oflex
pip install -r requirements.txt
```
Add an Anthropic API key — get one free at console.anthropic.com. Either set it as an environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```
Or copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and fill in the key.
Then:
```bash
streamlit run streamlit_app.py
```
The app will open at `http://localhost:8501`.
To run the tests:
```bash
pytest tests/ -v
```
You should see 22 passing tests.
---
Demo walkthrough
Open the sidebar to navigate. The intended flow:
Welcome — sets expectations, off-ramp to 1-866-866-0800 always visible.
Email check — applicant without email gets a step-by-step Proton Mail walkthrough (free, no phone number required).
Tell us about you — 7 plain-language questions. For "where did you sleep last night?" picking "Something else" lets you describe in free text — Claude translates the answer into the HIFIS `current_sleeping_location` enum.
Privacy choices — applicant picks sharing scope, purposes, and data categories in plain language. The system enforces non-empty purpose codes before save.
Review & next steps — plain-language summary, then consent-aware duplicate detection runs against the kit's full 800-client dataset. Try it twice:
With sharing scope `org` ("just this agency"): all matches blocked, fail-safe message shown.
With sharing scope `ca_table` ("agencies coordinating housing"): non-OCAP matches visible; OCAP-protected matches still blocked with "coordinator must review".
Coordinator view (demo page) — shows judges how the same data looks through our gates from any of the 9 partner orgs. Visualizes the gating count and surfaces all seeded `RED_FLAG_*` consent records.
The help assistant is available in the sidebar on every page. Try asking it "I don't have a SIN card" or something off-topic to see the scope guard fire.
---
Repository layout
```
oflex/
├── streamlit_app.py              # entry point
├── app/
│   ├── schema.py                 # HIFIS-aligned dataclasses + enums
│   ├── privacy_gates.py          # the 4 non-negotiable rules, in pure Python
│   ├── duplicate_detector.py     # Soundex + similarity baseline
│   ├── ai_layer.py               # Claude API: translation, summary, help
│   ├── help_chat.py              # scoped sidebar help assistant
│   ├── pdf_summary.py            # printable takeaway PDF generator
│   └── pages/                    # one Streamlit page per intake step
├── data/                         # starter kit sample CSVs, copied in
├── tests/test_privacy_gates.py   # 22 tests
├── requirements.txt
└── README.md
```
---
What we'd build next
If we had another week:
Replace the baseline duplicate detector with Splink (Bayesian entity resolution), which the kit explicitly recommends. Our consent-aware display layer would sit on top unchanged.
Add a worker review queue where Ministry workers see pending intakes and approve merge-or-keep decisions, completing the workflow loop.
Voice input for low-literacy clients who can't type.
In-app translation for the top 5 languages spoken in Victoria's unhoused community (the Ministry phone line already provides interpreters).
Wire `ORG-MSD` as a real entry in the kit's `organizations` table with proper DSAs to the existing 9 orgs.
---
Acknowledgements & data attribution
Data: BuildersVault Social Services Hackathon starter kit (synthetic), CC BY 4.0.
Stakeholder interviews:
Ministry of Social Development (MySelfServe team)
Cool Aid Health Centre — Victoria
Our Place Society — 919 Pandora Ave, Victoria
We are grateful for the time and candor these teams gave us during hackathon week. Any errors of representation are ours.
---
License
Code: MIT (see LICENSE).
Synthetic data shipped in `data/` is from the starter kit and is licensed under CC BY 4.0.
