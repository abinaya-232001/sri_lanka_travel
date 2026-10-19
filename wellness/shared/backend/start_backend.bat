@echo off
cd /d "%~dp0"
if exist .venv\Scripts\activate (
  call .venv\Scripts\activate
)
echo Starting Tour Ceylon backend on http://127.0.0.1:5002
python run.py
