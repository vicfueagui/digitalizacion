@echo off
setlocal
cd /d "%~dp0"
if not exist "%~dp0python_web_ruta.txt" (
    echo Falta completar la activacion web. No se abrira una base distinta.
    pause
    exit /b 1
)
set "DIG_WEB_PYTHON="
set /p "DIG_WEB_PYTHON="<"%~dp0python_web_ruta.txt"
if not exist "%DIG_WEB_PYTHON%" (
    echo No se encuentra el entorno Python verificado. Conserva la carpeta de runtime.
    pause
    exit /b 1
)
"%DIG_WEB_PYTHON%" -B "%~dp0iniciar_web.py" --workspace "%~dp0." --operacion
set "DIG_WEB_RESULT=%ERRORLEVEL%"
if not "%DIG_WEB_RESULT%"=="0" pause
exit /b %DIG_WEB_RESULT%
