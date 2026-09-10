@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ======================================================================
rem ORGANIZADOR DE TIFF POR CURP - VERSION 2
rem Compatible con Windows 7 / CMD
rem
rem Reglas actuales conservadas:
rem   DP-*.tif / DP-*.tiff -> PERSONALES
rem   FP-*.tif / FP-*.tiff -> PERSONALES
rem   HL-*.tif / HL-*.tiff -> FEDERAL
rem
rem Mejoras principales:
rem   - Captura digitalizador y conteo fisico opcional.
rem   - Cuenta TIFF finales reales en la carpeta CURP.
rem   - Resume por DP / FP / HL y por PERSONALES / FEDERAL.
rem   - Registra INDIVIDUAL vs MULTI sin confundir MULTI con paginas TIFF.
rem   - Detecta TIFF sueltos, conflictos, errores y archivos no esperados.
rem   - Genera resumen TXT, CSV e historial de ejecucion.
rem   - Genera CONTROL_DIGITALIZACION.csv acumulado en la carpeta ESCANER.
rem ======================================================================

cd /d "%~dp0"
title Organizador de TIFF por CURP - v2

set "CONTROL_GLOBAL=%CD%\CONTROL_DIGITALIZACION.csv"

echo ======================================================================
echo             ORGANIZADOR DE TIFF POR CURP - VERSION 2
echo ======================================================================
echo.
echo Carpeta de trabajo:
echo %CD%
echo.

rem ----------------------------------------------------------------------
rem 1. CAPTURA DE DATOS BASICOS
rem ----------------------------------------------------------------------

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
set "CURP=!CURP: =!"

rem Validar longitud exacta de 18 caracteres.
if "!CURP:~17,1!"=="" (
    echo.
    echo ERROR: La CURP tiene menos de 18 caracteres.
    echo.
    goto PEDIR_CURP
)

if not "!CURP:~18,1!"=="" (
    echo.
    echo ERROR: La CURP tiene mas de 18 caracteres.
    echo.
    goto PEDIR_CURP
)

rem Validar que solo contenga letras y numeros.
echo(!CURP!| findstr /r /x "[A-Za-z0-9][A-Za-z0-9]*" >nul
if errorlevel 1 (
    echo.
    echo ERROR: La CURP solo puede contener letras y numeros.
    echo.
    goto PEDIR_CURP
)

set "DIGITALIZADOR="
set /p "DIGITALIZADOR=Nombre o identificador del digitalizador [%USERNAME%]: "
if not defined DIGITALIZADOR set "DIGITALIZADOR=%USERNAME%"
rem Evitar romper archivos CSV separados por punto y coma.
set "DIGITALIZADOR=!DIGITALIZADOR:;=,!"

:PEDIR_FISICOS
set "FISICOS="
set /p "FISICOS=Cantidad de hojas fisicas (Enter para omitir): "
if not defined FISICOS (
    set "FISICOS=NO_CAPTURADO"
    goto DATOS_LISTOS
)

for /f "delims=0123456789" %%A in ("!FISICOS!") do (
    echo.
    echo ERROR: El conteo fisico debe contener solo numeros enteros.
    echo.
    goto PEDIR_FISICOS
)

:DATOS_LISTOS
set "DESTINO=%CD%\!CURP!"
set "PERSONALES=!DESTINO!\PERSONALES"
set "FEDERAL=!DESTINO!\FEDERAL"
set "RESUMEN_TXT=!DESTINO!\RESUMEN_DIGITALIZACION.txt"
set "RESUMEN_CSV=!DESTINO!\RESUMEN_DIGITALIZACION.csv"
set "HISTORIAL_LOG=!DESTINO!\HISTORIAL_ORGANIZACION.log"

rem ----------------------------------------------------------------------
rem 2. PREPARAR ESTRUCTURA
rem ----------------------------------------------------------------------

if not exist "!DESTINO!\" md "!DESTINO!"
if errorlevel 1 goto ERROR_CARPETA

if not exist "!PERSONALES!\" md "!PERSONALES!"
if errorlevel 1 goto ERROR_CARPETA

if not exist "!FEDERAL!\" md "!FEDERAL!"
if errorlevel 1 goto ERROR_CARPETA

call :CONTAR_TIFF_CARPETA "!PERSONALES!" PRE_PERSONALES
call :CONTAR_TIFF_CARPETA "!FEDERAL!" PRE_FEDERAL
set /a PREEXISTENTES=PRE_PERSONALES+PRE_FEDERAL

echo.
echo Estructura preparada:
echo   !CURP!
echo     PERSONALES
echo     FEDERAL
echo.

if !PREEXISTENTES! GTR 0 (
    echo AVISO: La carpeta CURP ya contenia !PREEXISTENTES! archivo(s) TIFF.
    echo        El resumen final mostrara el total acumulado existente.
    echo.
)

call :CONTAR_TIFF_CARPETA "%CD%" TIFF_ORIGEN

echo TIFF detectados en la carpeta ESCANER antes de organizar: !TIFF_ORIGEN!
echo ------------------------------------------------------------
dir /b /a-d "*.tif" 2^>nul
dir /b /a-d "*.tiff" 2^>nul
echo ------------------------------------------------------------
echo.

rem ----------------------------------------------------------------------
rem 3. MOVER ARCHIVOS SEGUN PREFIJO
rem ----------------------------------------------------------------------

set /a MOV_PERSONALES=0
set /a MOV_FEDERAL=0
set /a CONFLICTOS=0
set /a ERRORES=0

echo Moviendo DP- y FP- a PERSONALES...

for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff") do (
    if exist "%%~fF" (
        if exist "!PERSONALES!\%%~nxF" (
            echo [CONFLICTO] %%~nxF ya existe en PERSONALES. No se movio.
            set /a CONFLICTOS+=1
        ) else (
            move /Y "%%~fF" "!PERSONALES!\" >nul
            if errorlevel 1 (
                echo [ERROR] No se pudo mover %%~nxF
                set /a ERRORES+=1
            ) else (
                echo [OK] %%~nxF -^> PERSONALES
                set /a MOV_PERSONALES+=1
            )
        )
    )
)

echo.
echo Moviendo HL- a FEDERAL...

for %%F in ("HL-*.tif" "HL-*.tiff") do (
    if exist "%%~fF" (
        if exist "!FEDERAL!\%%~nxF" (
            echo [CONFLICTO] %%~nxF ya existe en FEDERAL. No se movio.
            set /a CONFLICTOS+=1
        ) else (
            move /Y "%%~fF" "!FEDERAL!\" >nul
            if errorlevel 1 (
                echo [ERROR] No se pudo mover %%~nxF
                set /a ERRORES+=1
            ) else (
                echo [OK] %%~nxF -^> FEDERAL
                set /a MOV_FEDERAL+=1
            )
        )
    )
)

rem ----------------------------------------------------------------------
rem 4. CONTEO FINAL REAL DE LA CARPETA CURP
rem ----------------------------------------------------------------------

call :CONTAR_TIFF_CARPETA "!PERSONALES!" TOTAL_PERSONALES
call :CONTAR_TIFF_CARPETA "!FEDERAL!" TOTAL_FEDERAL
call :CONTAR_TIFF_CARPETA "!DESTINO!" TOTAL_RAIZ_CURP
set /a TOTAL_DIGITALES=TOTAL_PERSONALES+TOTAL_FEDERAL+TOTAL_RAIZ_CURP

call :CONTAR_PATRON "!PERSONALES!" "DP-*.tif" DP_TIF
call :CONTAR_PATRON "!PERSONALES!" "DP-*.tiff" DP_TIFF
set /a TOTAL_DP=DP_TIF+DP_TIFF

call :CONTAR_PATRON "!PERSONALES!" "FP-*.tif" FP_TIF
call :CONTAR_PATRON "!PERSONALES!" "FP-*.tiff" FP_TIFF
set /a TOTAL_FP=FP_TIF+FP_TIFF

call :CONTAR_PATRON "!FEDERAL!" "HL-*.tif" HL_TIF
call :CONTAR_PATRON "!FEDERAL!" "HL-*.tiff" HL_TIFF
set /a TOTAL_HL=HL_TIF+HL_TIFF

set /a TOTAL_ESPERADOS=TOTAL_DP+TOTAL_FP+TOTAL_HL
set /a OTROS_DESTINO=TOTAL_DIGITALES-TOTAL_ESPERADOS
set /a MOV_TOTAL=MOV_PERSONALES+MOV_FEDERAL

call :CONTAR_TIFF_CARPETA "%CD%" TIFF_SUELTOS

rem ----------------------------------------------------------------------
rem 5. CAPTURA DE MODALIDAD INDIVIDUAL / MULTI
rem ----------------------------------------------------------------------
rem IMPORTANTE:
rem MULTI no se deduce por el numero de paginas del TIFF.
rem Un TIFF individual, por ejemplo METLIFE, puede contener dos paginas.
rem Por eso el usuario registra cuantos ARCHIVOS TIFF corresponden a MULTI.
rem ----------------------------------------------------------------------

if !TOTAL_DIGITALES! EQU 0 (
    set "MULTI=0"
    set "INDIVIDUALES=0"
    goto MODALIDAD_LISTA
)

:PEDIR_MULTI
set "MULTI="
echo.
echo La carpeta CURP contiene !TOTAL_DIGITALES! archivo(s) TIFF en total.
echo IMPORTANTE: MULTI significa documento trabajado con modalidad MULTI,
echo no simplemente un TIFF que tenga mas de una pagina.
set /p "MULTI=Cuantos TIFF del expediente corresponden a MULTI? [0]: "
if not defined MULTI set "MULTI=0"

for /f "delims=0123456789" %%A in ("!MULTI!") do (
    echo.
    echo ERROR: MULTI debe ser un numero entero entre 0 y !TOTAL_DIGITALES!.
    goto PEDIR_MULTI
)

if !MULTI! GTR !TOTAL_DIGITALES! (
    echo.
    echo ERROR: MULTI no puede ser mayor que el total de digitales.
    goto PEDIR_MULTI
)

set /a INDIVIDUALES=TOTAL_DIGITALES-MULTI

:MODALIDAD_LISTA
rem ----------------------------------------------------------------------
rem 6. EVALUAR RESULTADO DE ORGANIZACION
rem ----------------------------------------------------------------------

set "RESULTADO=OK"
if !CONFLICTOS! GTR 0 set "RESULTADO=REVISAR"
if !ERRORES! GTR 0 set "RESULTADO=REVISAR"
if !TIFF_SUELTOS! GTR 0 set "RESULTADO=REVISAR"
if !OTROS_DESTINO! GTR 0 set "RESULTADO=REVISAR"
if !TOTAL_DIGITALES! EQU 0 set "RESULTADO=SIN_DIGITALES"

set "FECHA=%DATE%"
set "HORA=%TIME:~0,8%"
set "APUNTE_FOLDER=Digitales !TOTAL_DIGITALES!, Fecha !FECHA!, Digitalizador: !DIGITALIZADOR!"

rem ----------------------------------------------------------------------
rem 7. GENERAR EVIDENCIAS / RESUMENES
rem ----------------------------------------------------------------------

>"!RESUMEN_TXT!" echo ============================================================
>>"!RESUMEN_TXT!" echo RESUMEN DE DIGITALIZACION / ORGANIZACION TIFF
>>"!RESUMEN_TXT!" echo ============================================================
>>"!RESUMEN_TXT!" echo CURP: !CURP!
>>"!RESUMEN_TXT!" echo Fecha: !FECHA!
>>"!RESUMEN_TXT!" echo Hora: !HORA!
>>"!RESUMEN_TXT!" echo Digitalizador: !DIGITALIZADOR!
>>"!RESUMEN_TXT!" echo Hojas fisicas: !FISICOS!
>>"!RESUMEN_TXT!" echo.
>>"!RESUMEN_TXT!" echo TOTAL DIGITALES TIFF: !TOTAL_DIGITALES!
>>"!RESUMEN_TXT!" echo   PERSONALES: !TOTAL_PERSONALES!
>>"!RESUMEN_TXT!" echo     DP-: !TOTAL_DP!
>>"!RESUMEN_TXT!" echo     FP-: !TOTAL_FP!
>>"!RESUMEN_TXT!" echo   FEDERAL: !TOTAL_FEDERAL!
>>"!RESUMEN_TXT!" echo     HL-: !TOTAL_HL!
>>"!RESUMEN_TXT!" echo   TIFF directamente en raiz CURP: !TOTAL_RAIZ_CURP!
>>"!RESUMEN_TXT!" echo.
>>"!RESUMEN_TXT!" echo MODALIDAD DE TRABAJO:
>>"!RESUMEN_TXT!" echo   INDIVIDUALES: !INDIVIDUALES!
>>"!RESUMEN_TXT!" echo   MULTI: !MULTI!
>>"!RESUMEN_TXT!" echo.
>>"!RESUMEN_TXT!" echo CONTROL DE ORGANIZACION:
>>"!RESUMEN_TXT!" echo   Movidos en esta ejecucion: !MOV_TOTAL!
>>"!RESUMEN_TXT!" echo   Conflictos: !CONFLICTOS!
>>"!RESUMEN_TXT!" echo   Errores de movimiento: !ERRORES!
>>"!RESUMEN_TXT!" echo   TIFF sueltos en ESCANER: !TIFF_SUELTOS!
>>"!RESUMEN_TXT!" echo   TIFF no esperados dentro de CURP: !OTROS_DESTINO!
>>"!RESUMEN_TXT!" echo   Resultado organizacion: !RESULTADO!
>>"!RESUMEN_TXT!" echo.
>>"!RESUMEN_TXT!" echo APUNTE SUGERIDO PARA EL FOLDER FISICO:
>>"!RESUMEN_TXT!" echo !APUNTE_FOLDER!
>>"!RESUMEN_TXT!" echo ============================================================

>"!RESUMEN_CSV!" echo CURP;FECHA;HORA;DIGITALIZADOR;FISICOS;DIGITALES;INDIVIDUALES;MULTI;PERSONALES;FEDERAL;TIFF_RAIZ_CURP;DP;FP;HL;MOVIDOS_EJECUCION;CONFLICTOS;ERRORES;TIFF_SUELTOS;OTROS_DESTINO;RESULTADO
>>"!RESUMEN_CSV!" echo !CURP!;!FECHA!;!HORA!;!DIGITALIZADOR!;!FISICOS!;!TOTAL_DIGITALES!;!INDIVIDUALES!;!MULTI!;!TOTAL_PERSONALES!;!TOTAL_FEDERAL!;!TOTAL_RAIZ_CURP!;!TOTAL_DP!;!TOTAL_FP!;!TOTAL_HL!;!MOV_TOTAL!;!CONFLICTOS!;!ERRORES!;!TIFF_SUELTOS!;!OTROS_DESTINO!;!RESULTADO!

>>"!HISTORIAL_LOG!" echo [!FECHA! !HORA!] Digitalizador=!DIGITALIZADOR! ^| Fisicos=!FISICOS! ^| Digitales=!TOTAL_DIGITALES! ^| Individuales=!INDIVIDUALES! ^| Multi=!MULTI! ^| Movidos=!MOV_TOTAL! ^| Conflictos=!CONFLICTOS! ^| Errores=!ERRORES! ^| Sueltos=!TIFF_SUELTOS! ^| Resultado=!RESULTADO!

if not exist "!CONTROL_GLOBAL!" (
    >"!CONTROL_GLOBAL!" echo CURP;FECHA;HORA;DIGITALIZADOR;FISICOS;DIGITALES;INDIVIDUALES;MULTI;PERSONALES;FEDERAL;TIFF_RAIZ_CURP;DP;FP;HL;MOVIDOS_EJECUCION;CONFLICTOS;ERRORES;TIFF_SUELTOS;OTROS_DESTINO;RESULTADO
)
>>"!CONTROL_GLOBAL!" echo !CURP!;!FECHA!;!HORA!;!DIGITALIZADOR!;!FISICOS!;!TOTAL_DIGITALES!;!INDIVIDUALES!;!MULTI!;!TOTAL_PERSONALES!;!TOTAL_FEDERAL!;!TOTAL_RAIZ_CURP!;!TOTAL_DP!;!TOTAL_FP!;!TOTAL_HL!;!MOV_TOTAL!;!CONFLICTOS!;!ERRORES!;!TIFF_SUELTOS!;!OTROS_DESTINO!;!RESULTADO!

rem ----------------------------------------------------------------------
rem 8. RESUMEN EN PANTALLA
rem ----------------------------------------------------------------------

echo.
echo ======================================================================
echo                              RESUMEN
echo ======================================================================
echo CURP                 : !CURP!
echo Digitalizador        : !DIGITALIZADOR!
echo Hojas fisicas        : !FISICOS!
echo ----------------------------------------------------------------------
echo Total digitales TIFF : !TOTAL_DIGITALES!
echo   Individuales       : !INDIVIDUALES!
echo   Multi              : !MULTI!
echo ----------------------------------------------------------------------
echo PERSONALES            : !TOTAL_PERSONALES!
echo   DP-                 : !TOTAL_DP!
echo   FP-                 : !TOTAL_FP!
echo FEDERAL               : !TOTAL_FEDERAL!
echo   HL-                 : !TOTAL_HL!
echo TIFF raiz de CURP     : !TOTAL_RAIZ_CURP!
echo ----------------------------------------------------------------------
echo Movidos esta ejecucion: !MOV_TOTAL!
echo Conflictos            : !CONFLICTOS!
echo Errores movimiento    : !ERRORES!
echo TIFF sueltos ESCANER  : !TIFF_SUELTOS!
echo TIFF no esperados CURP: !OTROS_DESTINO!
echo ----------------------------------------------------------------------
echo Resultado organizacion: !RESULTADO!
echo ======================================================================
echo.
echo Apunte sugerido para el folder fisico:
echo !APUNTE_FOLDER!
echo.
echo Se generaron:
echo   !RESUMEN_TXT!
echo   !RESUMEN_CSV!
echo   !HISTORIAL_LOG!
echo.
echo Control acumulado para varias CURP:
echo   !CONTROL_GLOBAL!
echo.

if !TIFF_SUELTOS! GTR 0 (
    echo TIFF que quedaron sueltos en la carpeta ESCANER:
    echo ------------------------------------------------------------
    dir /b /a-d "*.tif" 2^>nul
    dir /b /a-d "*.tiff" 2^>nul
    echo ------------------------------------------------------------
    echo Revise nombres, conflictos o prefijos no reconocidos.
    echo.
)

if /i "!RESULTADO!"=="OK" (
    echo La organizacion de archivos no presenta alertas automaticas.
    echo Esto NO sustituye la validacion humana del expediente.
) else (
    echo ATENCION: El resultado requiere revision antes de cerrar el expediente.
)

echo.
pause
goto FIN

:ERROR_CARPETA
echo.
echo ERROR: No fue posible crear la estructura de carpetas.
echo Por seguridad, revise permisos, ruta y espacio disponible.
echo.
pause
goto FIN

rem ======================================================================
rem SUBRUTINAS DE CONTEO
rem ======================================================================

:CONTAR_TIFF_CARPETA
set /a _CUENTA=0
for %%F in ("%~1\*.tif" "%~1\*.tiff") do (
    if exist "%%~fF" set /a _CUENTA+=1
)
set "%~2=!_CUENTA!"
exit /b

:CONTAR_PATRON
set /a _CUENTA=0
for %%F in ("%~1\%~2") do (
    if exist "%%~fF" set /a _CUENTA+=1
)
set "%~3=!_CUENTA!"
exit /b

:FIN
endlocal
