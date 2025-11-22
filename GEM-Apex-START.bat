@echo off
title GEM-Apex Dossier Architect
color 0A

echo.
echo  ╔════════════════════════════════════════╗
echo  ║   GEM-Apex Dossier Architect          ║
echo  ║   Professional Character Generator     ║
echo  ╚════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo [1/2] Checking Python installation...
python --version
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python from python.org
    pause
    exit
)

echo.
echo [2/2] Starting application...
python src\main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start!
    echo Check the error message above.
    echo.
    pause
)
