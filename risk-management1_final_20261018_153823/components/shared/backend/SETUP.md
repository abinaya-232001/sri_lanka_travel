# Unified backend setup

Open Command Prompt or PowerShell in this folder:

```text
D:\ceylon kalin\ceylon\components\shared\backend
```

Install the requirements using the file in the current folder:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The previous command failed because `components\shared\backend\requirements.txt` was entered while already inside `components\shared\backend`. That path incorrectly repeats the current folder.

Start the backend with the virtual-environment interpreter:

```powershell
.venv\Scripts\python.exe run.py
```

Or double-click `start_backend.bat`. The batch file creates the environment if needed, installs `requirements.txt`, and always starts the backend with `.venv\Scripts\python.exe`.

The backend listens on `http://127.0.0.1:5002`.

## Start the frontends

Keep the backend terminal running. In a second terminal, from `components`:

```powershell
cd "D:\ceylon kalin\ceylon\components"
npm install
npm run dev:itinerary
```

The itinerary frontend is available at `http://localhost:5180` and proxies `/api` requests to the backend on port `5002`.

To start all frontends together instead:

```powershell
npm run install:all
npm run dev
```

Press `Ctrl+C` only when you want to stop the development servers. After stopping them, `localhost:5180` will correctly show `ERR_CONNECTION_REFUSED` until the itinerary frontend is started again.