<!-- ONE-FRONTEND-SETUP -->
# Tourism Risk & Context Intelligence System - crowd/risk component (R26-IT-152)

Keep the folder structure as it is: the frontend imports from ..\..\..\tourism-unified and components\shared\frontend.

## 0. Scope of this submission

Only two pages are connected to this component's backend and are meant to be run and integrated:

    tourism-unified\src\pages\tourist\Discover.jsx
    tourism-unified\src\pages\tourist\DestinationDetail.jsx

The other pages in tourism-unified\src\pages belong to the group's shared frontend and are included unchanged
so the folder structure and imports stay intact. They are not connected to this backend, so they may show
empty data or errors when run on their own. This is expected.

## 1. Backend (Windows PowerShell, Python 3.10, scikit-learn 1.7.1 is pinned because the models were trained with it)

    cd <this folder>\components\risk-management\backend
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python app.py

The API starts on http://127.0.0.1:5000. Start-up must print "Models loaded successfully" and "Loaded 197 sites".
Optional settings (environment variables): PORT, HOST, FLASK_DEBUG=1, CORS_ORIGINS (comma separated).

PostgreSQL is optional. Crowd prediction, forecast, explanation, ranking and the other endpoints used by the
two pages do not need it. Only /error-analysis needs it (it returns a 503 message without a database).
To enable it, create an empty database, set these variables in the same PowerShell window and run python database.py:

    $env:DB_HOST = "localhost"
    $env:DB_PORT = "5432"
    $env:DB_NAME = "tourism_risk_db"
    $env:DB_USER = "postgres"
    $env:DB_PASSWORD = "<your postgres password>"

## 2. Frontend (second PowerShell window)

    cd <this folder>\components\risk-management\frontend
    npm install
    npm run dev

Open http://localhost:5182 and use the Discover page, then open one destination (DestinationDetail).
The dev server forwards /api/risk/... to the backend.
Defaults: VITE_API_TARGET=http://127.0.0.1:5000 and VITE_API_STRIP_PREFIX=1 (the standalone backend has no /api/risk prefix).
For the group unified backend (which mounts /api/risk) set VITE_API_STRIP_PREFIX=0 and VITE_API_TARGET to its address.
The weather panel calls the public Open-Meteo service, so it needs internet access.

## 3. Dataset, models and validation

Dataset: backend\data\master_dataset_fixed.csv (144,007 rows, 197 sites).
Models: backend\models (trained from that file, see models\model_metadata.json).
Reproduce the validation: backend\scripts\validate_model.py (reference site-holdout MAE 0.1232, R2 0.3331).
Retraining: backend\scripts\train_model.py.
