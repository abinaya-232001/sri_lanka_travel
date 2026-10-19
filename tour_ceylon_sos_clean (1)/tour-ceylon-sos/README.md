# Tour Ceylon SOS

Emergency help for tourists in Sri Lanka. Only this flow — nothing else:

1. **Tourist dashboard**: a search bar with an **SOS** button. Type what is happening, or tap the
   mic and speak, then press SOS. (Nothing typed = one-tap SOS.)
2. **Voice → English**: the voice note is transcribed and translated to English.
3. **Incident type**: a Random Forest model (trained on 4,950 tourist messages, 15 incident
   types, 92.3% accuracy on unseen messages) identifies the incident.
4. **Tips + contact numbers** on the tourist dashboard: highlighted safety tip, nearest police
   station (tap to call), and the numbers for that incident (ambulance 1990, fire 110, …).
5. **Nearest police station dashboard** gets the SOS instantly with the message and the
   tourist's **live location**, which keeps updating — and the **route** is drawn — until the
   **tourist** turns it off.
6. **Chat** between the tourist and that station: text, photos and voice notes, live,
   with translation both ways.
7. **WhatsApp to family** right after SOS: every number in the tourist's **Safety card** gets the
   emergency, a Google Maps link and the police station alerted.

Each police station has its own login and sees only its own cases.

```
backend/   Flask + Socket.IO + SQLite/PostgreSQL + Random Forest model
frontend/  React (Vite): tourist app at /  ·  police dashboard at /police
```

## Run it

**Backend** (Python 3.10+)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # then edit the secrets
python scripts/seed.py --demo                          # stations, hospitals, police logins, demo tourist
python run.py                                          # http://localhost:5000
```
`seed.py` loads 581 police stations, 41 tourism police stations and 37 hospitals from `data/`,
and creates one login per station (e.g. `ella-police`) with a **random** temporary password in
`data/officer_credentials.csv`. Give each station its own line, then delete the file. Officers
must set their own password at first login.

**Frontend** (Node 18+)
```bash
cd frontend
npm install
npm run dev                                            # http://localhost:5173
```
Tourist: open `/` (demo: `demo@tourceylon.lk` / `demo12345`). Police: open `/police/login`.

## WhatsApp to family

A website cannot send WhatsApp messages by itself; it needs the WhatsApp Business API. This uses
**Twilio**. In `backend/.env`:
```
WHATSAPP_MODE=twilio
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886     # Twilio sandbox for testing
TWILIO_WHATSAPP_CONTENT_SID=HX...              # production: your approved template
```
* Testing (sandbox): each family phone must first send the sandbox "join" code to the Twilio number.
* Production: WhatsApp only allows business-started messages through an **approved template**.
  Create one with 4 variables — {{1}} tourist name, {{2}} emergency, {{3}} map link,
  {{4}} police station — and put its SID in `TWILIO_WHATSAPP_CONTENT_SID`.
* Until this is set up (`WHATSAPP_MODE=console`), the tourist sees a **Send on WhatsApp** button
  per family member with the message already written — one tap to send.

## Voice in any language

With `OPENAI_API_KEY` set, Whisper translates the voice note directly to English. Without it,
the browser's speech recognition transcript (Chrome, Edge, Safari) is translated to English.

## Model

`backend/app/ml/` — retrain after adding messages to `backend/data/tourist_incident_dataset.csv`:
```bash
cd backend && python -m app.ml.train_incident_model
```
Low-confidence predictions are flagged "AI unsure" on the police dashboard, and the type is
updated when the tourist sends a clearer follow-up message.

## Tests
```bash
cd backend && pytest
```
27 tests: full SOS flow, voice SOS, station isolation, live location on/off, chat with photos and
voice, media privacy, WhatsApp via Twilio, socket room security, the model.

## Before going live
* Set long random `SECRET_KEY` and `JWT_SECRET_KEY`; use PostgreSQL (`DATABASE_URL`) and HTTPS
  (browsers only allow GPS and microphone on HTTPS).
* Your reverse proxy must forward `/socket.io` with WebSocket upgrade headers.
* Verify the hotline numbers in `backend/app/services/guidance.py` and station phone numbers.
* Browsers pause GPS when the phone is locked or the app is in the background; live location is
  reliable while the app is open. True background tracking needs a native (e.g. Capacitor) app.
