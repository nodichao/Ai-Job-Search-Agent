# AI Job Search Agent -- frontend

A minimal Streamlit interface for the POC: import a CV, set preferences, click one button, see the results the backend's existing search/matching/recommendation engine produced.

This app contains **no business logic**. It never imports the backend's matching engine or services; it only calls `POST /api/agent/search` on the backend API and renders exactly what it returns (scores, ranks, and recommendation decisions are never recomputed here).

## Run locally

The backend must already be running (see `../backend/README.md`), with at least one connector enabled (e.g. `HIMALAYAS_ENABLED=true`, the default) and `GROQ_API_KEY` configured if you want real AI-generated explanations -- the search itself still works and falls back to a deterministic explanation if the LLM is unavailable.

```sh
python -m venv .venv
source .venv/Scripts/activate   # .venv\Scripts\activate on Windows cmd/PowerShell, .venv/bin/activate on Linux/macOS
pip install -r requirements.txt
streamlit run app.py
```

By default the app calls the backend at `http://localhost:8000`. To point it elsewhere:

```sh
export JOB_AGENT_API_URL=http://localhost:8000   # $env:JOB_AGENT_API_URL = "..." on PowerShell
```

`JOB_AGENT_API_TIMEOUT_SECONDS` (default `120`) bounds how long the app waits for a response; the backend call is synchronous (extract CV → search → explain), so a full run can take from a few seconds up to roughly a minute depending on the connectors and LLM latency.

## What it does

1. Upload a CV (PDF or DOCX, 5 MiB max -- the same limit the backend enforces).
2. Choose preferences from simple dropdowns/checkboxes (job titles, location, work mode, seniority, contract type, salary, skills). "Sans préférence" always maps to an empty/absent value, never a fabricated constraint.
3. Click **"Rechercher des offres"** (disabled until a valid CV is selected).
4. The app shows a loading spinner while the backend runs the full workflow, then displays:
   - the real per-offer scores, recommendation decisions, and matching evidence from the engine;
   - the explanation for each shown offer (AI-generated, or a clearly labeled deterministic fallback if the AI explanation service was unavailable);
   - the engine's own ranking order (recommended offers first);
   - a toggle to also show offers the engine did not recommend;
   - the real list of steps the backend agent executed (not a simulated progress bar -- the backend call is synchronous, so this trace is shown after the response arrives, not "live").

## Known limitations

- No prefill of preferences from the CV before search: since the workflow is a single request/response call, the frontend cannot see the extracted profile until after the search completes. Preference fields (job titles, skills, etc.) are entered independently of the CV.
- "Afrique" / "Partout dans le monde" location choices are not translated into a country filter (the backend's `SearchPreferences` model has no continent/region concept); the UI says so explicitly rather than guessing a country list.
- This app has been syntax-checked and its request/response parsing reviewed line-by-line against the actual backend response models, but has not been exercised in a running browser in this environment (the development machine ran out of disk space while installing Streamlit's dependencies). Please do a first manual run before a live demo.
