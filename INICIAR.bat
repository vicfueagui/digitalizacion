@echo off
setlocal
cd /d "%~dp0"
set "DIG_PYTHON="
call :pick_python
if not defined DIG_PYTHON (
    echo No se encontro un Python compatible para Digitalizacion.
    echo Se requiere CPython 3.8.10 de 64 bits con Tk y Pillow 9.5.0/TIFF.
    echo Consulta ACTUALIZACION.html antes de continuar.
    pause
    exit /b 1
)
"%DIG_PYTHON%" main.py %*
set "DIG_RESULT=%ERRORLEVEL%"
if not "%DIG_RESULT%"=="0" echo La operacion fallo. Revisa el mensaje anterior.
pause
exit /b %DIG_RESULT%

:pick_python
call :try_python "%~dp0.venv\Scripts\python.exe"
if defined DIG_PYTHON exit /b 0
if exist "%~dp0python_ruta.txt" (
    for /f "usebackq delims=" %%P in ("%~dp0python_ruta.txt") do if not defined DIG_PYTHON call :try_python "%%~P"
)
if defined DIG_PYTHON exit /b 0
call :try_python "%LocalAppData%\Programs\Python\Python38\python.exe"
if defined DIG_PYTHON exit /b 0
call :try_python "C:\Python38\python.exe"
exit /b 0

:try_python
if "%~1"=="" exit /b 0
if not exist "%~1" exit /b 0
for %%I in ("%~1") do if %%~zI LEQ 0 exit /b 0
"%~1" -c "import sys,struct,tkinter,PIL; from PIL import features; assert sys.version_info[:3]==(3,8,10) and struct.calcsize('P')==8 and PIL.__version__=='9.5.0' and features.check('libtiff')" >nul 2>&1
if errorlevel 1 exit /b 0
set "DIG_PYTHON=%~1"
exit /b 0
