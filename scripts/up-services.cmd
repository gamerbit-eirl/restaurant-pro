@echo off
setlocal

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0up-services.ps1" %*
exit /b %ERRORLEVEL%
