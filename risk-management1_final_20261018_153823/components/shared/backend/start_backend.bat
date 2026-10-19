@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
  echo Creating Python virtual environment in %CD%\.venv
  py -3 -m venv .venv
  if errorlevel 1 (
    echo Failed to create the virtual environment.
    exit /b 1
  )
)
echo Installing backend dependencies from %CD%\requirements.txt
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
  echo Failed to install backend dependencies.
  exit /b 1
)
echo Starting Tour Ceylon backend on http://127.0.0.1:5002
.venv\Scripts\python.exe run.py
