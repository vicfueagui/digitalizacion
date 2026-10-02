@echo off
setlocal
set "PYTHONDONTWRITEBYTECODE=1"
set "CONTEXTO_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%CONTEXTO_PYTHON%" (
    echo No se encontro el interprete existente del proyecto. No se instalara nada.
    exit /b 1
)
"%CONTEXTO_PYTHON%" -B "%~dp0tools\exportar_contexto.py" --raiz "%~dp0."
exit /b %ERRORLEVEL%
