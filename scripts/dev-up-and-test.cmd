@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0dev-up-and-test.ps1" %*
set EXIT_CODE=%ERRORLEVEL%

if not "%EXIT_CODE%"=="0" (
  echo.
  echo Script finalizo con error %EXIT_CODE%.
)

exit /b %EXIT_CODE%
