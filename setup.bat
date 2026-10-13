@echo off
REM One-time setup: virtual environment + dependencies + ML dataset + ML model
cd /d "%~dp0"
python --version >nul 2>&1 || (echo Python is not installed or not on PATH. Install Python 3.10-3.12 first. & pause & exit /b 1)
if not exist venv python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend\requirements.txt || (echo Dependency install failed. & pause & exit /b 1)
python ml\generate_dataset.py
python ml\train_model.py
echo.
echo Setup complete. Now run:  run.bat
pause
