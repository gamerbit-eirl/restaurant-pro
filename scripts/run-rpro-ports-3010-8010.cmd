@echo off
setlocal

set API_HOST=%~1
if "%API_HOST%"=="" set API_HOST=127.0.0.1

set REPO=%~dp0..\
set BACKEND_DIR=%REPO%backend
set FRONTEND_DIR=%REPO%frontend
set PY=%REPO%.venv\Scripts\python.exe

if not exist "%PY%" (
  echo [ERROR] No existe %PY%
  exit /b 1
)

echo [Restaurant Pro] Backend -> http://%API_HOST%:8010
echo [Restaurant Pro] Frontend -> http://%API_HOST%:3010

start "RPRO Backend 8010" cmd /k "cd /d \"%BACKEND_DIR%\" && \"%PY%\" -m uvicorn app.main:app --host 0.0.0.0 --port 8010"
start "RPRO Frontend 3010" cmd /k "cd /d \"%FRONTEND_DIR%\" && set NEXT_PUBLIC_API_URL=http://%API_HOST%:8010&&npm run dev -- -H 0.0.0.0 -p 3010"

echo.
echo Abre: http://%API_HOST%:3010
echo API:  http://%API_HOST%:8010/docs
