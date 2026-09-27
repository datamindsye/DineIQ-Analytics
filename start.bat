@echo off
title DineIQ Analytics Launcher
echo ====================================================================
echo                   DineIQ Analytics Platform Launcher
echo ====================================================================
echo.

cd /d "%~dp0"

:: 1. Detect Python executable
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_CMD=.venv\Scripts\python.exe"
    echo [OK] Using virtual environment Python: .venv\Scripts\python.exe
) else (
    set "PYTHON_CMD=python"
    echo [INFO] Using system Python
)

:: 2. Start FastAPI Backend API in a separate terminal window
echo [1/3] Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "DineIQ Backend (Port 8000)" cmd /k "cd /d "%~dp0" && %PYTHON_CMD% -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --reload"

:: 3. Start React + Vite Frontend in a separate terminal window
echo [2/3] Starting React / Vite Frontend on http://localhost:5173 ...
start "DineIQ Frontend (Port 5173)" cmd /k "cd /d "%~dp0apps\web" && npm run dev"

:: 4. Brief delay to allow Vite and FastAPI to bind ports
echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

:: 5. Open Default Browser
echo [OK] Launching browser at http://localhost:5173/ ...
start http://localhost:5173/

echo.
echo ====================================================================
echo  DineIQ Analytics services are running!
echo.
echo  - Frontend Dashboard:  http://localhost:5173/
echo  - Backend REST API:    http://127.0.0.1:8000/
echo  - Interactive Swagger: http://127.0.0.1:8000/docs
echo  - Health Probe:        http://127.0.0.1:8000/api/v1/health
echo.
echo  Keep the opened terminal windows running while using the platform.
echo  To shut down, simply close the backend and frontend terminal windows.
echo ====================================================================
echo.
pause
