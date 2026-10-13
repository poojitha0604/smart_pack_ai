@echo off
REM Starts the SmartPack AI website at http://localhost:5000
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first. & pause & exit /b 1)
call venv\Scripts\activate
cd backend
start "" http://localhost:5000
python app.py
pause
