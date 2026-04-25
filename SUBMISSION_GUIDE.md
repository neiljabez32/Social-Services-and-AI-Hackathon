# How to Submit to GitHub & Devpost

This is a step-by-step guide for getting Oflex up on GitHub and linked to Devpost. Written for someone who hasn't done this before.

---

## Part 1: Get the code on GitHub

### Option A — using the GitHub website (easiest, no command line)

1. Go to **github.com** and sign in (or create a free account).
2. In the top right, click the **+** icon → **New repository**.
3. Fill in:
   - **Repository name:** `oflex`
   - **Description:** `Plain-language front door to BC Income Assistance — BuildersVault Hackathon Track 1`
   - **Public** (judges need to see it)
   - **Do not** check "Add a README" — we already have one.
   - **Do not** add a license through GitHub — we already have one.
4. Click **Create repository**.
5. On the new repo page, click **uploading an existing file**.
6. Drag the contents of the `oflex/` folder into the upload area. Important: drag the **contents**, not the folder itself. You should see `streamlit_app.py`, `README.md`, the `app/` folder, etc., at the top level.
7. Scroll down. Commit message: `Initial commit — Oflex submission`.
8. Click **Commit changes**.

That's it — the repo is live.

### Option B — using the command line (if you're comfortable with git)

```bash
cd path/to/oflex
git init
git add .
git commit -m "Initial commit — Oflex submission"
git branch -M main
git remote add origin https://github.com/<your-username>/oflex.git
git push -u origin main
```

---

## Part 2: Verify the repo looks right

Open your repo URL (`https://github.com/<your-username>/oflex`) and check:

- [ ] The README displays at the bottom of the page with project name, track, and team (edit the team field if you haven't yet).
- [ ] `LICENSE`, `PRIVACY.md`, and `DEVPOST.md` are all visible at the top level.
- [ ] The `app/`, `data/`, and `tests/` folders are there.
- [ ] `requirements.txt` is at the top level.
- [ ] **`.streamlit/secrets.toml` is NOT in the repo** (only `.streamlit/secrets.toml.example` should be there). If you accidentally uploaded the real secrets file, delete it through the GitHub UI immediately and rotate your API key.

---

## Part 3: Optional — deploy a live demo (recommended by judges)

Streamlit Cloud is free and takes about 5 minutes:

1. Go to **streamlit.io/cloud** and sign in with GitHub.
2. Click **New app**.
3. Pick the `oflex` repo, branch `main`, main file `streamlit_app.py`.
4. Click **Advanced settings** → **Secrets**, and paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   ```
5. Click **Deploy**. Wait 2-3 minutes for the first build.
6. Once it's live, copy the URL (something like `https://oflex-xyz.streamlit.app`).

Add the Streamlit Cloud URL to:
- The README (replace the `_[Streamlit Cloud URL...]_` placeholder)
- The Devpost "Try it out links" section

---

## Part 4: Record your demo video

Use the script in `_[your demo script file]_` (the 3-minute walkthrough). Tools that work well:

- **Loom** (loom.com) — simplest. Free tier, 5-minute videos.
- **OBS Studio** — free, more control.
- **macOS:** Cmd+Shift+5 → built-in screen recorder.

Upload the video to YouTube (unlisted) or keep it on Loom. Copy the share URL.

Add the URL to:
- The README (replace the `_[YouTube/Loom link]_` placeholder)
- The Devpost video field

---

## Part 5: Submit to Devpost

1. Go to the BuildersVault Hackathon's Devpost page.
2. Click **Submit a project**.
3. Open `DEVPOST.md` from this repo. Each section maps to a Devpost form field — paste them in.
4. Set:
   - **Try it out links:** GitHub URL + Streamlit Cloud URL (if deployed)
   - **Video demo URL:** your recording
   - **Tags / Built With:** streamlit, anthropic-claude, python, reportlab
5. Add team members by their email addresses on Devpost (each must have a Devpost account).
6. Save as draft, review once, then submit.

---

## Last-minute sanity checks before you hit submit

- [ ] Team names are filled in on the README (replace `_[your names here — edit before submitting]_`)
- [ ] Demo video URL is in the README and on Devpost
- [ ] Live demo URL is in the README and on Devpost (if deployed)
- [ ] `pytest tests/ -v` runs clean — 22 passing — on a fresh clone
- [ ] No real API keys committed anywhere
- [ ] Devpost team list matches the README
- [ ] Track is set to **Inter-Org Referral & Care Coordination** on Devpost

Good luck Saturday.
