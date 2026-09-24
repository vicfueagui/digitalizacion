@echo off
setlocal DisableDelayedExpansion
call "%~dp0EJECUTAR.bat" actualizar %*
set "DIG_RESULT=%ERRORLEVEL%"
if not "%DIG_RESULT%"=="0" echo La operacion se detuvo. Revise el mensaje anterior.
pause
exit /b %DIG_RESULT%
