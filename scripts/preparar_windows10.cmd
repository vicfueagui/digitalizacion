@echo off
setlocal EnableExtensions
chcp 65001 >nul

for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"
set "VENV_DIR=%PROJECT_DIR%\.venv-windows"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

cd /d "%PROJECT_DIR%"
if errorlevel 1 goto ERROR

if exist "%VENV_PYTHON%" goto VENV_READY
if exist "%VENV_DIR%\" goto INVALID_VENV

where py >nul 2>nul
if errorlevel 1 goto TRY_PYTHON
py -3.12 -c "import sys; raise SystemExit(sys.version_info < (3, 12))" >nul 2>nul
if errorlevel 1 goto TRY_PYTHON
set "PYTHON_COMMAND=py -3.12"
goto CREATE_VENV

:TRY_PYTHON
where python >nul 2>nul
if errorlevel 1 goto PYTHON_MISSING
python -c "import sys; raise SystemExit(sys.version_info < (3, 12))" >nul 2>nul
if errorlevel 1 goto PYTHON_MISSING
set "PYTHON_COMMAND=python"

:CREATE_VENV
echo Creando entorno virtual de Windows con %PYTHON_COMMAND%...
%PYTHON_COMMAND% -m venv "%VENV_DIR%"
if errorlevel 1 goto ERROR

:VENV_READY
echo Instalando dependencias del proyecto...
"%VENV_PYTHON%" -m pip install -r requirements.txt
if errorlevel 1 goto ERROR

echo Preparando configuración local privada...
"%VENV_PYTHON%" scripts\prepare_local_env.py
if errorlevel 1 goto ERROR

echo Aplicando migraciones...
"%VENV_PYTHON%" manage.py migrate --noinput
if errorlevel 1 goto ERROR

echo Cargando catálogos y permisos iniciales...
"%VENV_PYTHON%" manage.py initialize_system
if errorlevel 1 goto ERROR

echo Verificando la instalación...
"%VENV_PYTHON%" manage.py check
if errorlevel 1 goto ERROR

echo.
echo Preparación terminada correctamente.
echo Para crear una cuenta administradora ejecute:
echo   .venv-windows\Scripts\python.exe manage.py createsuperuser
echo.
echo Después abra scripts\iniciar_windows10.cmd.
if /I "%~1"=="--no-pause" goto SUCCESS
pause

:SUCCESS
endlocal
exit /b 0

:INVALID_VENV
echo ERROR: .venv-windows existe, pero no contiene un entorno Python utilizable. >&2
echo Renombre esa carpeta y vuelva a ejecutar la preparación. >&2
goto ERROR_WITHOUT_MESSAGE

:PYTHON_MISSING
echo ERROR: No se encontró Python 3.12 o posterior. >&2
echo Instale Python 3.12 para Windows y active la opción Add Python to PATH. >&2
goto ERROR_WITHOUT_MESSAGE

:ERROR
echo ERROR: La preparación no pudo completarse. Revise el mensaje anterior. >&2

:ERROR_WITHOUT_MESSAGE
if /I "%~1"=="--no-pause" goto FAILURE
pause

:FAILURE
endlocal
exit /b 1
