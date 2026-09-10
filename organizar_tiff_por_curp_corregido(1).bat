@echo off
setlocal EnableExtensions

rem ============================================================
rem ORGANIZADOR DE TIFF POR CURP - Windows 7
rem Version simplificada y robusta
rem
rem DP-*.tif / DP-*.tiff  -> PERSONALES
rem FP-*.tif / FP-*.tiff  -> PERSONALES
rem HL-*.tif / HL-*.tiff  -> FEDERAL
rem ============================================================

cd /d "%~dp0"
title Organizador de TIFF por CURP

echo ============================================================
echo               ORGANIZADOR DE TIFF POR CURP
echo ============================================================
echo.
echo Carpeta de trabajo:
echo %CD%
echo.

:PEDIR_CURP
set "CURP="
set /p "CURP=Ingrese la CURP del expediente: "

if not defined CURP (
    echo.
    echo ERROR: Debe ingresar una CURP.
    echo.
    goto PEDIR_CURP
)

rem Quitar espacios accidentales.
set "CURP=%CURP: =%"

rem Validar longitud de 18 caracteres.
if "%CURP:~17,1%"=="" (
    echo.
    echo ERROR: La CURP tiene menos de 18 caracteres.
    echo.
    goto PEDIR_CURP
)

if not "%CURP:~18,1%"=="" (
    echo.
    echo ERROR: La CURP tiene mas de 18 caracteres.
    echo.
    goto PEDIR_CURP
)

set "DESTINO=%CD%\%CURP%"
set "PERSONALES=%DESTINO%\PERSONALES"
set "FEDERAL=%DESTINO%\FEDERAL"

if not exist "%DESTINO%\" md "%DESTINO%"
if errorlevel 1 goto ERROR_CARPETA

if not exist "%PERSONALES%\" md "%PERSONALES%"
if errorlevel 1 goto ERROR_CARPETA

if not exist "%FEDERAL%\" md "%FEDERAL%"
if errorlevel 1 goto ERROR_CARPETA

echo.
echo Estructura preparada:
echo   %CURP%
echo     PERSONALES
echo     FEDERAL
echo.

echo TIFF que Windows detecta antes de organizar:
echo ------------------------------------------------------------
dir /b /a-d "*.tif" 2^>nul
dir /b /a-d "*.tiff" 2^>nul
echo ------------------------------------------------------------
echo.

set /a PERSONAL=0
set /a FED=0
set /a CONFLICTOS=0

echo Moviendo DP- y FP- a PERSONALES...

for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff") do (
    if exist "%%~fF" (
        if exist "%PERSONALES%\%%~nxF" (
            echo [CONFLICTO] %%~nxF ya existe en PERSONALES. No se movio.
            set /a CONFLICTOS+=1
        ) else (
            move /Y "%%~fF" "%PERSONALES%\" >nul
            if errorlevel 1 (
                echo [ERROR] No se pudo mover %%~nxF
            ) else (
                echo [OK] %%~nxF -^> PERSONALES
                set /a PERSONAL+=1
            )
        )
    )
)

echo.
echo Moviendo HL- a FEDERAL...

for %%F in ("HL-*.tif" "HL-*.tiff") do (
    if exist "%%~fF" (
        if exist "%FEDERAL%\%%~nxF" (
            echo [CONFLICTO] %%~nxF ya existe en FEDERAL. No se movio.
            set /a CONFLICTOS+=1
        ) else (
            move /Y "%%~fF" "%FEDERAL%\" >nul
            if errorlevel 1 (
                echo [ERROR] No se pudo mover %%~nxF
            ) else (
                echo [OK] %%~nxF -^> FEDERAL
                set /a FED+=1
            )
        )
    )
)

echo.
echo ============================================================
echo                         RESUMEN
echo ============================================================
echo Movidos a PERSONALES: %PERSONAL%
echo Movidos a FEDERAL   : %FED%
echo Conflictos          : %CONFLICTOS%
echo ============================================================
echo.

echo TIFF que quedaron sueltos en la carpeta ESCANER:
echo ------------------------------------------------------------
dir /b /a-d "*.tif" 2^>nul
dir /b /a-d "*.tiff" 2^>nul
echo ------------------------------------------------------------
echo.
echo Si no aparece ningun archivo arriba, el proceso termino bien.
echo Si aparece alguno, revise que su nombre empiece exactamente
echo con DP-, FP- o HL-.
echo.
pause
goto FIN

:ERROR_CARPETA
echo.
echo ERROR: No fue posible crear la estructura de carpetas.
echo No se movio ningun archivo.
echo.
pause

:FIN
endlocal
