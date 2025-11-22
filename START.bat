@echo off
echo ====================================
echo  GEM-Apex Dossier Architect
echo  Starting...
echo ====================================
echo.

cd /d "%~dp0"

echo Installing dependencies (if needed)...
pip install -r requirements.txt --quiet

echo.
echo Starting application...
python src\main.py

pause
