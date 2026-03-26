@echo off
setlocal

set REPO_DIR=%~dp0..\
cd /d "%REPO_DIR%backend"

python scripts\seed_and_workload.py %*
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
  echo.
  echo seed_and_workload fallo con codigo %EXIT_CODE%.
)

exit /b %EXIT_CODE%
