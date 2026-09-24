@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0ejecutar_python.ps1" "%~dp0." %*
exit /b %ERRORLEVEL%
