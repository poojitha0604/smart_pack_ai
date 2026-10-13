@echo off
REM Builds datasets\images from downloads\ (if present), checks it, and trains the food-photo model.
cd /d "%~dp0"
if not exist venv (echo Run setup.bat first. & pause & exit /b 1)
call venv\Scripts\activate
pip install -r dl\requirements.txt || (echo TensorFlow install failed - use Python 3.10-3.12 64-bit. & pause & exit /b 1)
if exist downloads\fruitveg python datasets\prepare_dataset.py --fruitveg downloads\fruitveg --max-per-class 150
if exist downloads\food11 python datasets\prepare_dataset.py --food11 downloads\food11 --max-per-class 150
python datasets\prepare_dataset.py --check
echo.
echo If a class has too few images or potato_chips is empty, add images first (see README section 4). Press any key to start training.
pause
python dl\train_model.py
pause
