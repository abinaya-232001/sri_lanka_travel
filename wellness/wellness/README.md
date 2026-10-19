# Tour Ceylon — Ayurveda & Spiritual Tourism Matching System

A full-stack research prototype: Python backend (Flask + trained ML model) serving
a browser-based matching interface for Ayurvedic treatment and spiritual retreat
centers across Sri Lanka.

---

## Project Structure

```
tour_ceylon_project/
├── backend/
│   ├── app.py                  ← Flask server (serves the API AND the frontend)
│   ├── matching_engine.py      ← core logic: dosha model, matching, cost, risk detection
│   ├── schema.sql               ← MySQL database schema + real data (optional, for a real DB)
│   └── data/
│       ├── full_candidate_pool.json
│       └── tourist_profiles_training_data.xlsx
│
└── frontend/
    ├── index.html               ← page structure
    ├── css/
    │   └── style.css            ← all styling
    ├── js/
    │   └── app.js                ← all interactive logic (calls the backend API)
    └── images/                    ← real photo files (not embedded/base64)
```

**This is now genuinely connected** — the frontend's core matching (`runMatch()`) and
scenario comparison (`runScenarioCompare()`) call the real Python backend over HTTP
(`/api/recommend`, `/api/match`), which runs the actual trained dosha classifier and
matching engine. This is not a JS-only demo anymore.

---

## How to Run

### Step 1 — Install Python packages

Open a terminal in the `backend/` folder and run:

```bash
pip install flask pandas scikit-learn openpyxl numpy --break-system-packages
```

### Step 2 — Start the server

Still inside `backend/`:

```bash
python app.py
```

You should see:
```
Loaded 83 centers. Ready at http://localhost:5003
* Running on http://127.0.0.1:5003
```

### Step 3 — Open the app

Open your browser and go to:

```
http://localhost:5003
```

**That's it** — one server, serves both the UI and the API. No separate frontend
server needed, no CORS setup needed (everything is same-origin).

---

## What's Actually Connected vs What's Local

Being precise about this, since it matters for how you describe the system:

| Feature | Connected to Python backend? |
|---|---|
| Dosha prediction + main matching (`Find My Match` / `Find My Retreat`) | ✅ Yes — calls `/api/recommend` |
| "Try a Different Scenario" comparison | ✅ Yes — calls `/api/match` (twice, in parallel) |
| Browse All Centers (search/filter) | ❌ No — reads the same `full_candidate_pool.json` data directly in JS (no matching/scoring happens here, just filtering a list, so there was nothing to "connect") |
| Risk flag detection on detail pages | Computed client-side in JS from the review text already included in the API response (same logic as backend, just run twice — harmless, not a bug) |
| Map View, Cost Calculator, Language toggle, Session patterns | These operate on data already returned by `/api/recommend` — no additional network calls needed |

If you want Browse Mode to also hit the backend (e.g. so a future login system can log what tourists search), that's a small additional endpoint (`/api/centers` already exists and returns exactly this data) — just needs the JS in `renderBrowse()` to fetch it instead of reading the local `POOL` variable. Not done here since Browse Mode doesn't do any scoring/matching that needs the ML model.

---

## API Endpoints (backend/app.py)

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Serves the frontend (index.html) |
| GET | `/api/health` | Health check |
| GET | `/api/centers?path=ayurveda` | List centers for a path |
| GET | `/api/conditions?path=spiritual` | List condition options |
| POST | `/api/recommend` | Main matching (predicts dosha + returns ranked centers) |
| POST | `/api/match` | Matching with a known dosha (used for scenario comparison) |
| GET | `/api/center/<name>` | Full detail for one center |
| POST | `/api/cost-estimate` | Trip cost calculator |

---

## Database (Optional)

`backend/schema.sql` sets up a real MySQL database with the same data currently
read from `full_candidate_pool.json`. The backend doesn't use this yet — it reads
the JSON file directly, which is simpler for a research prototype. If you want the
backend to read from MySQL instead of the JSON file, that's a further step (swap
`matching_engine.py`'s data loading from `json.load()` to a database query) — not
done here to keep the current setup simple and dependency-light for grading/demo
purposes.

---

## Common Problems

**"ModuleNotFoundError"** → Step 1 didn't complete, re-run the pip install.

**Blank page / images missing at localhost:5003** → Make sure you're running
`python app.py` from inside the `backend/` folder specifically (it looks for
`../frontend` relative to itself).

**"Could not reach the matching server" alert in the browser** → The backend isn't
running, or crashed. Check the terminal where you ran `python app.py` for errors.

**Port 5003 already in use** → Close whatever else is using it, or change the port
number in `app.py` (`app.run(..., port=5003)`).

---

## Admin Dashboard

A password-protected admin dashboard is available at `http://localhost:5003/admin`.

**Password:** `tourceylon2026`

⚠️ **Honest note on security:** this is demo-grade auth — a single shared password,
not a real user/role system. Fine for a local demo or FYP presentation; would need
proper authentication (per-admin accounts, hashed passwords, HTTPS) before any real
deployment.

**What it does:**
- **Analytics tab** — live stats (centers by category/dosha, avg quality score,
  flagged review counts) plus your actual model development results (dosha classifier
  comparison, ablation study) pulled from `backend/data/model_comparison_results.csv`
  and `backend/data/ablation_results.json`.
- **Centers tab** — full CRUD: search, edit any center's details, add new centers,
  delete centers. Edits are written back to `backend/data/full_candidate_pool.json`,
  so they persist across server restarts.
- **Flagged Reviews tab** — every review the safety keyword-detector flagged, grouped
  by center, so you can review them manually.

## Handing This to a Teammate

Send the entire `tour_ceylon_project/` folder (zipped). They only need to follow
"How to Run" above — everything (data, model training data, images) is self-contained.

