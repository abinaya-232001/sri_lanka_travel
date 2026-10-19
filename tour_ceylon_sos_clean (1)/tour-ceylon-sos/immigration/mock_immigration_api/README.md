# Immigration API integration

The immigration dashboard now gets visa details from the Department of Immigration and Emigration API instead of what the tourist types in.

## Run with the mock API (development / demo)

1. Start the mock immigration API:

       cd mock_immigration_api
       pip install flask
       python app.py                 # http://localhost:5055

2. Set these for the SOS backend (`.env` or config):

       IMMIGRATION_API_URL=http://localhost:5055
       IMMIGRATION_API_KEY=demo-immigration-key

3. Add the new columns:

       python backend/migrate_sos_ext.py

4. Open the immigration dashboard and press **Sync from Immigration API**.

Demo passports are in `travellers.json` (match by passport number + nationality). Dates there are offsets from today.

## Switching to the real API

Change only `IMMIGRATION_API_URL` and `IMMIGRATION_API_KEY`. If the real API's field names differ, adjust `fetch_visa_status()` / `sync_tourist()` in `backend/services/immigration_api_client.py`. Access to the real API needs written authorization from the Department.

## When data is pulled

- Tourist registers → passport checked automatically.
- Tourist changes passport or nationality in Profile → checked again.
- Immigration officer presses **Sync from Immigration API** → all tourists.

Once verified, visa type and expiry are locked in the tourist's profile.
