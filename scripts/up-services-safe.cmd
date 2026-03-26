@echo off
setlocal

set API_HOST=%~1
if "%API_HOST%"=="" set API_HOST=127.0.0.1

set REPO=%~dp0..\
set BACKEND_PY=%REPO%.venv\Scripts\python.exe

if not exist "%BACKEND_PY%" (
  echo [ERROR] No existe %BACKEND_PY%
  exit /b 1
)

echo [Restaurant Pro] Levantando backend en http://%API_HOST%:8001
start "RPRO-BACKEND" /D "%REPO%backend" cmd /k "\"%BACKEND_PY%\" -m uvicorn app.main:app --host 0.0.0.0 --port 8001"

echo [Restaurant Pro] Levantando frontend en http://%API_HOST%:3000
start "RPRO-FRONTEND" /D "%REPO%frontend" cmd /k "set NEXT_PUBLIC_API_URL=http://%API_HOST%:8001&&npm run dev -- -H 0.0.0.0 -p 3000"

echo.
echo Frontend: http://%API_HOST%:3000
echo Backend:  http://%API_HOST%:8001
echo Docs:     http://%API_HOST%:8001/docs
