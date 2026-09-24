@echo off
setlocal DisableDelayedExpansion
call "%~dp0EJECUTAR.bat" integridad %*
set "DIG_RESULT=%ERRORLEVEL%"
if not "%DIG_RESULT%"=="0" echo La operacion se detuvo. Revise el mensaje anterior.
pause
exit /b %DIG_RESULT%
