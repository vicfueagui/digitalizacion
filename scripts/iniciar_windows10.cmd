@echo off
setlocal EnableExtensions
chcp 65001 >nul

for %%I in ("%~dp0..") do set "PROJECT_DIR=%%~fI"
set "SETUP_SCRIPT=%~dp0preparar_windows10.cmd"
set "VENV_PYTHON=%PROJECT_DIR%\.venv-windows\Scripts\python.exe"
set "SERVER_HOST=127.0.0.1"
set "SERVER_PORT=%DIGITALIZACION_PORT%"
if not defined SERVER_PORT set "SERVER_PORT=8000"

cd /d "%PROJECT_DIR%"
if errorlevel 1 goto ERROR

echo(%SERVER_PORT%| %SystemRoot%\System32\findstr.exe /r /x "[0-9][0-9]*" >nul
if errorlevel 1 goto INVALID_PORT

if not exist "%VENV_PYTHON%" goto RUN_SETUP
if not exist "%PROJECT_DIR%\.env" goto RUN_SETUP
goto INSTALLATION_READY

:RUN_SETUP
echo La instalación local todavía no está preparada. Iniciando preparación...
call "%SETUP_SCRIPT%" --no-pause
if errorlevel 1 goto ERROR

:INSTALLATION_READY
"%VENV_PYTHON%" -c "p=int('%SERVER_PORT%'); raise SystemExit(not 1 <= p <= 65535)"
if errorlevel 1 goto INVALID_PORT

"%VENV_PYTHON%" manage.py check
if errorlevel 1 goto ERROR

"%VENV_PYTHON%" manage.py migrate --noinput
if errorlevel 1 goto ERROR

set "APP_URL=http://%SERVER_HOST%:%SERVER_PORT%/"

if "%DIGITALIZACION_OPEN_BROWSER%"=="0" goto START_SERVER
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -Command "$url='%APP_URL%'; for ($i=0; $i -lt 80; $i++) { try { Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 1 ^| Out-Null; Start-Process $url; exit 0 } catch { Start-Sleep -Milliseconds 250 } }"

:START_SERVER
echo.
echo Sistema disponible en %APP_URL%
echo La aplicación solo escucha en esta computadora.
echo Para detenerla presione Control+C en esta ventana.
echo.

"%VENV_PYTHON%" manage.py runserver "%SERVER_HOST%:%SERVER_PORT%" --noreload
set "SERVER_RESULT=%ERRORLEVEL%"
if "%DIGITALIZACION_NO_PAUSE%"=="1" goto DONE
echo.
echo Servidor detenido.
pause

:DONE
endlocal & exit /b %SERVER_RESULT%

:INVALID_PORT
echo ERROR: DIGITALIZACION_PORT debe ser un número entre 1 y 65535. >&2
goto ERROR_WITHOUT_MESSAGE

:ERROR
echo ERROR: No fue posible iniciar la aplicación. Revise el mensaje anterior. >&2

:ERROR_WITHOUT_MESSAGE
if "%DIGITALIZACION_NO_PAUSE%"=="1" goto FAILURE
pause

:FAILURE
endlocal
exit /b 1
