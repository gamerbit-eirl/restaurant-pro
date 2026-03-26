@echo off
setlocal

set REPO=%~dp0..\
set BACKEND_DIR=%REPO%backend
set FRONTEND_DIR=%REPO%frontend
set PY=%REPO%.venv\Scripts\python.exe

if not exist "%PY%" (
  echo [ERROR] No existe %PY%
  pause
  exit /b 1
)

echo [Restaurant Pro] Iniciando backend en 18010...
start "RPRO Backend 18010" cmd /k "cd /d \"%BACKEND_DIR%\" && \"%PY%\" -m uvicorn app.main:app --host 0.0.0.0 --port 18010"

timeout /t 2 >nul

echo [Restaurant Pro] Iniciando frontend en 13010...
cd /d "%FRONTEND_DIR%"
set NEXT_PUBLIC_API_URL=http://127.0.0.1:18010
npm run dev -- -H 0.0.0.0 -p 13010
