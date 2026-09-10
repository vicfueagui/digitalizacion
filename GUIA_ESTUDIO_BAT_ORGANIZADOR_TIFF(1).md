# Guía de estudio del BAT `organizar_tiff_por_curp_corregido.bat`

## 1. ¿Qué hace este archivo BAT?

Este archivo automatiza una tarea que antes hacías manualmente dentro de la carpeta **escaner**.

En términos simples, el programa hace esto:

1. Se asegura de trabajar en la misma carpeta donde está guardado el archivo `.bat`.
2. Te pide una CURP.
3. Comprueba que la CURP tenga 18 caracteres.
4. Crea una carpeta con esa CURP.
5. Dentro crea:
   - `PERSONALES`
   - `FEDERAL`
6. Busca archivos TIFF cuyos nombres empiecen con:
   - `DP-`
   - `FP-`
   - `HL-`
7. Mueve:
   - `DP-` y `FP-` a `PERSONALES`
   - `HL-` a `FEDERAL`
8. Evita reemplazar un archivo si ya existe otro con el mismo nombre.
9. Cuenta cuántos archivos movió.
10. Al final muestra qué archivos TIFF quedaron sueltos.

La idea general podría representarse así:

```text
ANTES

escaner\
│
├── organizar_tiff_por_curp_corregido.bat
├── DP-01.tif
├── DP-02.tif
├── FP-01.tif
├── HL-01.tif
└── HL-02.tif
```

Ingresas, por ejemplo:

```text
TESTA000000AAAAA01
```

Y el BAT deja:

```text
DESPUÉS

escaner\
│
├── organizar_tiff_por_curp_corregido.bat
│
└── TESTA000000AAAAA01\
    │
    ├── PERSONALES\
    │   ├── DP-01.tif
    │   ├── DP-02.tif
    │   └── FP-01.tif
    │
    └── FEDERAL\
        ├── HL-01.tif
        └── HL-02.tif
```

---

# 2. ¿Qué es un archivo BAT?

Un archivo `.bat` es, en términos sencillos, una **lista de instrucciones para Windows**.

Normalmente tú podrías abrir el Símbolo del sistema (`cmd`) y escribir comandos uno por uno:

```bat
md CARPETA
move archivo.tif CARPETA
dir
```

Un BAT permite guardar esas instrucciones en un archivo para que Windows las ejecute automáticamente en orden.

Es parecido a decirle a Windows:

> "Haz primero esto. Luego esto. Si pasa aquello, haz esto otro. Repite esta operación para todos los archivos que cumplan esta condición."

El lenguaje que utiliza es el lenguaje del **Símbolo del sistema de Windows**, también conocido como **CMD** o **Batch**.

---

# 3. El BAT completo que estamos estudiando

Este es el archivo que estás utilizando:

```bat
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
```

Ahora vamos a desarmarlo.

---

# 4. Primera línea: `@echo off`

```bat
@echo off
```

## ¿Qué significa?

Cuando Windows ejecuta un BAT, por defecto puede mostrar en pantalla los comandos que está ejecutando.

Por ejemplo, sin `echo off`, podrías ver algo parecido a:

```text
C:\escaner>set "CURP="
C:\escaner>set /p "CURP=Ingrese la CURP del expediente: "
C:\escaner>if not defined CURP ...
```

Eso ensucia mucho la pantalla.

Con:

```bat
echo off
```

le dices a Windows:

> "No muestres cada instrucción del programa. Muestra solamente lo que yo decida mostrar."

El símbolo:

```bat
@
```

evita que incluso la propia instrucción `echo off` aparezca en pantalla.

Por eso normalmente se escribe:

```bat
@echo off
```

### En cristiano

Es como activar el **modo limpio de pantalla**.

---

# 5. `setlocal EnableExtensions`

```bat
setlocal EnableExtensions
```

Aquí hay dos conceptos.

## `setlocal`

Le dice a Windows:

> "Las variables y cambios que haga este BAT serán locales a este programa."

Por ejemplo, el BAT crea:

```bat
CURP
DESTINO
PERSONALES
FEDERAL
PERSONAL
FED
CONFLICTOS
```

Gracias a `setlocal`, esas variables no deberían quedarse contaminando la sesión de CMD después de terminar el programa.

Al final encontrarás:

```bat
endlocal
```

Es decir:

```text
setlocal
   ↓
 empieza una zona de trabajo privada

... programa ...

endlocal
   ↓
 termina esa zona de trabajo
```

## `EnableExtensions`

Activa extensiones normales de CMD que permiten utilizar ciertas formas modernas de comandos.

En Windows 7 normalmente ya están disponibles, pero declararlo hace más explícito el comportamiento esperado.

### En cristiano

```bat
setlocal EnableExtensions
```

significa aproximadamente:

> "Voy a empezar mi propio espacio de trabajo y quiero usar las funciones normales ampliadas de CMD."

---

# 6. Los comentarios: `rem`

Ejemplo:

```bat
rem ORGANIZADOR DE TIFF POR CURP - Windows 7
```

`rem` significa **remark**, es decir, comentario.

Windows no ejecuta ese texto.

Sirve para dejar notas para la persona que lee el programa.

Por ejemplo:

```bat
rem Esto es un comentario
md CARPETA
```

Windows ignora:

```text
Esto es un comentario
```

y únicamente ejecuta:

```bat
md CARPETA
```

En tu programa usamos comentarios para documentar las reglas:

```bat
rem DP-*.tif / DP-*.tiff  -> PERSONALES
rem FP-*.tif / FP-*.tiff  -> PERSONALES
rem HL-*.tif / HL-*.tiff  -> FEDERAL
```

---

# 7. Una de las líneas más importantes: `%~dp0`

```bat
cd /d "%~dp0"
```

Esta línea merece especial atención.

## Primero: `cd`

`cd` significa **Change Directory**.

Es decir:

> "Cambia la carpeta de trabajo."

Ejemplo:

```bat
cd C:\escaner
```

haría que CMD trabajara dentro de:

```text
C:\escaner
```

## ¿Qué hace `/d`?

Permite cambiar también de unidad.

Por ejemplo, si el BAT se está ejecutando desde:

```text
C:
```

pero la carpeta `escaner` está en:

```text
D:
```

la opción `/d` permite cambiar correctamente de:

```text
C:
```

a:

```text
D:
```

además de cambiar de carpeta.

## ¿Qué demonios es `%~dp0`?

Es una variable especial de los archivos BAT.

Vamos a separarla:

```text
%0
```

representa el propio archivo BAT.

Por ejemplo:

```text
C:\escaner\organizar_tiff_por_curp_corregido.bat
```

Los modificadores:

```text
d
```

y:

```text
p
```

significan:

- `d` = drive = unidad
- `p` = path = ruta

Por eso:

```bat
%~dp0
```

significa:

> "Dame la unidad y la carpeta donde está guardado este mismo BAT."

Si el BAT está aquí:

```text
C:\Digitalizacion\escaner\organizar_tiff_por_curp_corregido.bat
```

entonces aproximadamente:

```bat
%~dp0
```

equivale a:

```text
C:\Digitalizacion\escaner\
```

Por tanto:

```bat
cd /d "%~dp0"
```

significa:

> "Trabaja dentro de la carpeta donde está guardado este BAT."

## ¿Por qué fue importante en tu problema?

Porque así evitamos depender de desde dónde Windows haya abierto el programa.

Nuestro BAT siempre dice:

> "Mi carpeta de trabajo será donde yo mismo estoy guardado."

Eso hace mucho más predecible dónde buscará los TIFF.

---

# 8. ¿Por qué usamos comillas?

Observa:

```bat
cd /d "%~dp0"
```

y no:

```bat
cd /d %~dp0
```

Las comillas protegen rutas que puedan contener espacios.

Por ejemplo:

```text
C:\Archivo General\Digitalizacion\escaner\
```

Sin comillas, Windows podría interpretar:

```text
C:\Archivo
```

como una cosa y:

```text
General\Digitalizacion\escaner
```

como otra.

Con:

```text
"C:\Archivo General\Digitalizacion\escaner\"
```

Windows entiende que todo es una sola ruta.

Esta regla aparece muchas veces en el BAT:

```bat
"%DESTINO%"
"%PERSONALES%"
"%FEDERAL%"
"%%~fF"
```

Es una buena práctica muy importante.

---

# 9. `title`

```bat
title Organizador de TIFF por CURP
```

Esto cambia el título de la ventana de CMD.

En lugar de que la ventana diga algo genérico, como:

```text
C:\Windows\system32\cmd.exe
```

puede mostrar:

```text
Organizador de TIFF por CURP
```

No afecta la lógica del programa. Es solamente presentación.

---

# 10. `echo`

Ejemplo:

```bat
echo Carpeta de trabajo:
```

`echo` imprime texto en pantalla.

Por ejemplo:

```bat
echo Hola Victor
```

muestra:

```text
Hola Victor
```

## ¿Qué significa `echo.`?

```bat
echo.
```

imprime una línea vacía.

Es equivalente visualmente a dejar un espacio entre párrafos.

Por eso el BAT utiliza muchos:

```bat
echo.
```

para que la pantalla sea más legible.

---

# 11. `%CD%`

```bat
echo %CD%
```

`%CD%` contiene el **Current Directory**, es decir, la carpeta actual de trabajo.

Si estamos trabajando en:

```text
C:\escaner
```

entonces:

```bat
echo %CD%
```

mostrará:

```text
C:\escaner
```

Esto es muy útil para diagnóstico.

Si algún día el BAT parece trabajar en una carpeta equivocada, esta línea te permite comprobar dónde cree Windows que está trabajando.

---

# 12. Las etiquetas: `:PEDIR_CURP`

```bat
:PEDIR_CURP
```

Una palabra que empieza con:

```text
:
```

es una **etiqueta**.

Puedes imaginarla como un letrero o punto de referencia dentro del programa.

Aquí tenemos tres:

```bat
:PEDIR_CURP
```

```bat
:ERROR_CARPETA
```

```bat
:FIN
```

Luego podemos utilizar:

```bat
goto PEDIR_CURP
```

para decir:

> "Salta directamente hasta la parte marcada como `:PEDIR_CURP`."

Esto permite crear repeticiones y rutas diferentes dentro del programa.

---

# 13. Crear una variable: `set`

```bat
set "CURP="
```

Esto crea o limpia la variable llamada:

```text
CURP
```

La forma:

```bat
set "CURP="
```

significa:

> "CURP ahora está vacía."

Es importante limpiarla antes de pedir una CURP nueva.

---

# 14. Pedir información al usuario: `set /p`

```bat
set /p "CURP=Ingrese la CURP del expediente: "
```

Esta instrucción detiene el programa y espera a que escribas algo.

Por ejemplo, Windows muestra:

```text
Ingrese la CURP del expediente:
```

Tú escribes:

```text
TESTA000000AAAAA01
```

Entonces la variable:

```text
CURP
```

pasa a contener:

```text
TESTA000000AAAAA01
```

Es decir:

```text
CURP = TESTA000000AAAAA01
```

Después podemos recuperar ese contenido escribiendo:

```bat
%CURP%
```

---

# 15. Cómo funcionan las variables `%VARIABLE%`

Supongamos:

```bat
set "CURP=TESTA000000AAAAA01"
```

Cuando Windows encuentra:

```bat
echo %CURP%
```

sustituye:

```text
%CURP%
```

por su contenido.

Por tanto ejecuta realmente algo parecido a:

```bat
echo TESTA000000AAAAA01
```

Lo mismo ocurre más adelante con:

```bat
%DESTINO%
%PERSONALES%
%FEDERAL%
%PERSONAL%
%FED%
%CONFLICTOS%
```

---

# 16. Primera validación: `if not defined`

```bat
if not defined CURP (
    echo.
    echo ERROR: Debe ingresar una CURP.
    echo.
    goto PEDIR_CURP
)
```

## `if`

`if` significa:

> "Si se cumple esta condición, haz algo."

## `defined CURP`

Pregunta:

> "¿La variable CURP contiene algo?"

## `not defined CURP`

Pregunta lo contrario:

> "¿CURP está vacía?"

Por tanto:

```bat
if not defined CURP (
```

significa:

> "Si el usuario no escribió ninguna CURP..."

entonces ejecuta todo lo que está entre:

```text
(
...
)
```

y finalmente:

```bat
goto PEDIR_CURP
```

lo manda otra vez al formulario de captura.

El flujo sería:

```text
Pedir CURP
   ↓
¿Está vacía?
   │
   ├── Sí → mostrar error → volver a pedirla
   │
   └── No → continuar
```

---

# 17. Eliminar espacios

```bat
set "CURP=%CURP: =%"
```

Esta sintaxis realiza una sustitución dentro de una variable.

La estructura general es:

```text
%VARIABLE:buscar=reemplazar%
```

Aquí tenemos:

```text
%CURP: =%
```

Después de los dos puntos hay:

```text
espacio =
```

pero después del signo `=` no hay nada.

Eso significa:

> "Busca espacios dentro de CURP y reemplázalos por nada."

Por ejemplo:

```text
DISL 760905 MYNZLR04
```

se convertiría en:

```text
TESTA000000AAAAA01
```

Esto ayuda contra espacios escritos accidentalmente.

---

# 18. Cómo verifica que la CURP tenga 18 caracteres

Esta parte parece extraña:

```bat
if "%CURP:~17,1%"=="" (
```

Vamos a entenderla.

## Extraer caracteres de una variable

CMD permite usar:

```text
%VARIABLE:~posición,cantidad%
```

Por ejemplo, si:

```text
CURP = ABCDEFGHIJKLMNOPQR
```

entonces:

```bat
%CURP:~0,1%
```

significa:

> "Desde la posición 0, dame 1 carácter."

Resultado:

```text
A
```

Otro ejemplo:

```bat
%CURP:~1,1%
```

resultado:

```text
B
```

Las posiciones comienzan en cero:

```text
A B C D E F ...
0 1 2 3 4 5 ...
```

Por eso el carácter número 18 está en la posición:

```text
17
```

---

# 19. Detectar una CURP demasiado corta

```bat
if "%CURP:~17,1%"=="" (
```

Pregunta:

> "¿Existe un carácter en la posición 17?"

Si no existe, la expresión queda vacía:

```text
""
```

Entonces sabemos que la CURP tiene menos de 18 caracteres.

Por eso muestra:

```bat
echo ERROR: La CURP tiene menos de 18 caracteres.
```

y vuelve a:

```bat
goto PEDIR_CURP
```

---

# 20. Detectar una CURP demasiado larga

Después tenemos:

```bat
if not "%CURP:~18,1%"=="" (
```

La posición:

```text
18
```

sería el carácter número 19.

Si existe un carácter número 19, sabemos que la CURP tiene más de 18 caracteres.

Entonces:

```bat
if not "%CURP:~18,1%"=="" (
```

significa aproximadamente:

> "Si la posición 18 NO está vacía, entonces existe un carácter número 19."

Por tanto:

```text
la CURP es demasiado larga
```

---

# 21. Importante: qué valida y qué NO valida

El BAT comprueba:

- que hayas escrito algo;
- que después de quitar espacios haya exactamente 18 caracteres.

No comprueba que la CURP sea oficialmente válida.

Por ejemplo, una cadena inventada de 18 caracteres podría superar esta validación.

El objetivo actual del BAT es evitar errores evidentes de captura, no actuar como un validador oficial completo de CURP.

---

# 22. Construcción de rutas

Estas tres líneas son fundamentales:

```bat
set "DESTINO=%CD%\%CURP%"
set "PERSONALES=%DESTINO%\PERSONALES"
set "FEDERAL=%DESTINO%\FEDERAL"
```

Vamos a simularlas.

Supongamos:

```text
%CD% = C:\escaner
```

y:

```text
%CURP% = TESTA000000AAAAA01
```

Entonces:

```bat
set "DESTINO=%CD%\%CURP%"
```

produce:

```text
DESTINO = C:\escaner\TESTA000000AAAAA01
```

Después:

```bat
set "PERSONALES=%DESTINO%\PERSONALES"
```

produce:

```text
PERSONALES = C:\escaner\TESTA000000AAAAA01\PERSONALES
```

Y:

```bat
set "FEDERAL=%DESTINO%\FEDERAL"
```

produce:

```text
FEDERAL = C:\escaner\TESTA000000AAAAA01\FEDERAL
```

Puedes pensar que estamos construyendo direcciones.

---

# 23. Crear carpetas: `md`

```bat
if not exist "%DESTINO%\" md "%DESTINO%"
```

## `exist`

Comprueba si algo existe.

## `not exist`

Comprueba si NO existe.

## `md`

Significa **Make Directory**:

> "Crear carpeta."

Por tanto la línea completa dice:

> "Si la carpeta DESTINO no existe, créala."

Ejemplo:

```bat
if not exist "C:\escaner\TESTA000000AAAAA01\" md "C:\escaner\TESTA000000AAAAA01"
```

Después repite la misma idea para:

```bat
PERSONALES
```

y:

```bat
FEDERAL
```

---

# 24. `errorlevel`: detectar si un comando falló

Después de crear una carpeta aparece:

```bat
if errorlevel 1 goto ERROR_CARPETA
```

Muchos comandos de Windows terminan guardando un código de resultado.

Normalmente:

```text
0 = funcionó
1 o más = ocurrió algún problema
```

Por eso:

```bat
if errorlevel 1
```

significa aproximadamente:

> "Si el comando anterior terminó con error..."

haz:

```bat
goto ERROR_CARPETA
```

Eso evita continuar con movimientos si la estructura de carpetas no pudo prepararse correctamente.

---

# 25. La ruta de error `:ERROR_CARPETA`

Más abajo encontramos:

```bat
:ERROR_CARPETA
echo.
echo ERROR: No fue posible crear la estructura de carpetas.
echo No se movio ningun archivo.
echo.
pause
```

Si la creación de carpetas falla, el programa salta aquí.

Por ejemplo, podría ocurrir si Windows no tiene permisos para escribir en esa ubicación.

El objetivo es **no seguir procesando archivos cuando la estructura necesaria no existe**.

---

# 26. `dir`: pedirle a Windows una lista de archivos

```bat
dir /b /a-d "*.tif" 2^>nul
```

`dir` sirve para listar archivos y carpetas.

La forma más sencilla sería:

```bat
dir
```

pero mostraría mucha información:

```text
fecha
hora
tamaño
<DIR>
...
```

Nuestro BAT utiliza opciones.

## `/b`

Significa **bare format**.

Muestra solamente los nombres.

En lugar de:

```text
04/09/2026  13:00     325,000 DP-01.tif
```

muestra:

```text
DP-01.tif
```

## `/a-d`

`/a` filtra por atributos.

El signo:

```text
-
```

significa excluir.

`d` significa directorios.

Por tanto:

```bat
/a-d
```

significa:

> "Muéstrame archivos, pero no carpetas."

## `"*.tif"`

El asterisco:

```text
*
```

es un **comodín**.

Significa:

> "Cualquier texto."

Por tanto:

```text
*.tif
```

significa:

> "Cualquier archivo cuyo nombre termine en `.tif`."

Ejemplos que coinciden:

```text
DP-01.tif
FP-27.tif
HL-123.tif
documento.tif
```

---

# 27. ¿Por qué también busca `.tiff`?

El BAT ejecuta:

```bat
dir /b /a-d "*.tif" 2^>nul
dir /b /a-d "*.tiff" 2^>nul
```

porque TIFF puede aparecer con dos extensiones habituales:

```text
.tif
```

o:

```text
.tiff
```

Así el programa admite ambas.

---

# 28. ¿Qué significa `2^>nul`?

Esta parte es más técnica:

```bat
2^>nul
```

Primero necesitas entender:

```text
nul
```

`nul` es una especie de agujero negro de Windows.

Todo lo enviado ahí desaparece.

Por ejemplo, si un comando genera un mensaje que no nos interesa, podemos mandarlo a:

```text
nul
```

El número:

```text
2
```

representa el canal de errores.

Conceptualmente:

```text
1 = salida normal
2 = salida de errores
```

Entonces:

```text
2>nul
```

significa:

> "Los mensajes de error no los muestres; mándalos a la nada."

El símbolo `^` sirve aquí para escapar el símbolo `>` dentro del contexto del BAT.

El objetivo práctico es evitar mensajes feos si, por ejemplo, no existen archivos `.tiff`.

---

# 29. Los contadores

```bat
set /a PERSONAL=0
set /a FED=0
set /a CONFLICTOS=0
```

La opción:

```bat
/a
```

indica que trabajaremos con números y operaciones aritméticas.

Creamos tres contadores:

```text
PERSONAL = archivos movidos a PERSONALES
FED = archivos movidos a FEDERAL
CONFLICTOS = archivos que no se movieron porque ya existía uno con el mismo nombre
```

Todos empiezan en:

```text
0
```

---

# 30. La parte más importante: el bucle `for`

Aquí comienza el motor que mueve varios archivos:

```bat
for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff") do (
```

`for` significa:

> "Repite una operación para cada elemento que cumpla estas condiciones."

Las condiciones son:

```text
DP-*.tif
DP-*.tiff
FP-*.tif
FP-*.tiff
```

Eso significa:

```text
archivos .tif que empiecen DP-
archivos .tiff que empiecen DP-
archivos .tif que empiecen FP-
archivos .tiff que empiecen FP-
```

Por ejemplo, si existen:

```text
DP-01.tif
DP-02.tif
FP-01.tif
HL-01.tif
```

este primer `for` trabajará solamente con:

```text
DP-01.tif
DP-02.tif
FP-01.tif
```

`HL-01.tif` no entra aquí porque tendrá su propio bucle.

---

# 31. ¿Qué es `%%F`?

Dentro de un BAT, una variable de un `for` normalmente se escribe con doble porcentaje:

```bat
%%F
```

Puedes imaginarla como una caja temporal.

Primera vuelta:

```text
%%F = DP-01.tif
```

Segunda vuelta:

```text
%%F = DP-02.tif
```

Tercera vuelta:

```text
%%F = FP-01.tif
```

Así el mismo bloque de instrucciones puede aplicarse a cada archivo.

---

# 32. ¿Por qué `F`?

No tiene un significado especial obligatorio.

Podríamos haber utilizado otra letra.

Por ejemplo:

```bat
%%A
```

o:

```bat
%%X
```

Pero `F` es intuitiva porque podemos pensar:

```text
F = File
```

---

# 33. `%%~fF`: obtener la ruta completa

Dentro del bucle aparece:

```bat
%%~fF
```

La `F` final es nuestra variable `%%F`.

El modificador:

```text
f
```

significa **full path**, ruta completa.

Por ejemplo, si:

```text
%%F = DP-01.tif
```

y estamos trabajando en:

```text
C:\escaner
```

entonces:

```bat
%%~fF
```

puede convertirse en:

```text
C:\escaner\DP-01.tif
```

Esto es más seguro que depender solamente del nombre.

---

# 34. `%%~nxF`: nombre y extensión

También aparece:

```bat
%%~nxF
```

Aquí:

```text
n = name
x = extension
```

Por tanto:

```bat
%%~nxF
```

significa:

> "Dame el nombre del archivo y su extensión, pero no toda la ruta."

Si:

```text
%%~fF
```

es:

```text
C:\escaner\DP-01.tif
```

entonces:

```text
%%~nxF
```

es:

```text
DP-01.tif
```

Esta diferencia es muy importante.

---

# 35. Tabla rápida de modificadores del `for`

Para un archivo:

```text
C:\escaner\DP-01.tif
```

puedes imaginar:

| Expresión | Resultado aproximado |
|---|---|
| `%%F` | archivo que está procesando el `for` |
| `%%~fF` | `C:\escaner\DP-01.tif` |
| `%%~nxF` | `DP-01.tif` |

En este BAT necesitamos principalmente:

- ruta completa para mover;
- nombre + extensión para comprobar conflictos y mostrar mensajes.

---

# 36. ¿Por qué vuelve a comprobar `if exist`?

```bat
if exist "%%~fF" (
```

Aunque el `for` trabaja con patrones como:

```text
DP-*.tif
```

esta comprobación confirma que realmente existe un archivo concreto antes de intentar moverlo.

Es una protección adicional.

---

# 37. Detección de archivos duplicados

Antes de mover, el BAT pregunta:

```bat
if exist "%PERSONALES%\%%~nxF" (
```

Vamos a traducirlo.

Supongamos:

```text
%PERSONALES% =
C:\escaner\TESTA000000AAAAA01\PERSONALES
```

y:

```text
%%~nxF = DP-01.tif
```

Windows comprueba:

```text
C:\escaner\TESTA000000AAAAA01\PERSONALES\DP-01.tif
```

La pregunta es:

> "¿Ya existe un `DP-01.tif` dentro de PERSONALES?"

Si sí existe, muestra:

```text
[CONFLICTO] DP-01.tif ya existe en PERSONALES. No se movio.
```

y aumenta:

```bat
set /a CONFLICTOS+=1
```

---

# 38. ¿Qué significa `+=1`?

```bat
set /a CONFLICTOS+=1
```

significa:

> "Toma el número actual de CONFLICTOS y súmale uno."

Si:

```text
CONFLICTOS = 0
```

después:

```text
CONFLICTOS = 1
```

Si vuelve a ocurrir:

```text
CONFLICTOS = 2
```

La misma técnica se utiliza con:

```bat
set /a PERSONAL+=1
```

y:

```bat
set /a FED+=1
```

---

# 39. `else`

Observa:

```bat
if exist "%PERSONALES%\%%~nxF" (
    ...
) else (
    ...
)
```

`else` significa:

> "Si NO se cumplió la condición anterior, haz esto otro."

Por tanto:

```text
¿Ya existe el archivo en PERSONALES?
       │
       ├── Sí → conflicto → no mover
       │
       └── No → intentar mover
```

---

# 40. El comando que realmente mueve el TIFF

Esta es una de las líneas centrales:

```bat
move /Y "%%~fF" "%PERSONALES%\" >nul
```

## `move`

Significa literalmente:

> "Mover un archivo."

No lo copia dejando el original.

Lo traslada del origen al destino.

## `"%%~fF"`

Es el archivo de origen.

Por ejemplo:

```text
C:\escaner\DP-01.tif
```

## `"%PERSONALES%\"`

Es el destino.

Por ejemplo:

```text
C:\escaner\TESTA000000AAAAA01\PERSONALES\
```

Conceptualmente Windows recibe algo parecido a:

```bat
move "C:\escaner\DP-01.tif" "C:\escaner\TESTA000000AAAAA01\PERSONALES\"
```

---

# 41. ¿Qué significa `/Y` en `move`?

```bat
move /Y
```

`/Y` indica a `move` que no pida confirmación interactiva para reemplazar.

Pero en nuestro programa **antes** comprobamos manualmente si ya existe el archivo:

```bat
if exist "%PERSONALES%\%%~nxF"
```

y si existe, no ejecutamos `move`.

Por tanto, la protección contra conflicto la controla nuestro propio código.

---

# 42. ¿Qué significa `>nul`?

Después del `move`:

```bat
>nul
```

manda la salida normal del comando al "agujero negro".

Sin eso, `move` podría mostrar mensajes propios de Windows.

Nosotros preferimos mostrar mensajes más claros:

```text
[OK] DP-01.tif -> PERSONALES
```

o:

```text
[ERROR] No se pudo mover DP-01.tif
```

Así controlamos lo que ve el usuario.

---

# 43. Comprobar si `move` funcionó

Justo después:

```bat
if errorlevel 1 (
    echo [ERROR] No se pudo mover %%~nxF
) else (
    echo [OK] %%~nxF -^> PERSONALES
    set /a PERSONAL+=1
)
```

La lógica es:

```text
Intentar mover archivo
       ↓
¿MOVE devolvió un error?
       │
       ├── Sí → mostrar [ERROR]
       │
       └── No → mostrar [OK] y sumar 1
```

Esto es muy importante porque el contador aumenta solamente si el movimiento fue exitoso.

---

# 44. ¿Por qué aparece `-^>`?

```bat
echo [OK] %%~nxF -^> PERSONALES
```

Lo que queremos mostrar visualmente es:

```text
DP-01.tif -> PERSONALES
```

Pero:

```text
>
```

tiene un significado especial en CMD: redirección.

Por eso usamos:

```text
^
```

para decir:

> "No interpretes `>` como una orden; quiero mostrarlo como un carácter normal."

Así:

```bat
-^>
```

termina apareciendo como:

```text
->
```

---

# 45. El segundo bucle: archivos `HL-`

Después tenemos:

```bat
for %%F in ("HL-*.tif" "HL-*.tiff") do (
```

La lógica es prácticamente idéntica al primer bucle.

La diferencia es el patrón:

```text
HL-*.tif
HL-*.tiff
```

y el destino:

```text
FEDERAL
```

Por ejemplo:

```text
HL-01.tif
HL-02.tiff
```

terminan en:

```text
CURP\FEDERAL\
```

---

# 46. ¿Por qué usamos dos bucles?

Podríamos haber construido una lógica más complicada que leyera cada archivo y preguntara cuál era su prefijo.

Sin embargo, para este proceso concreto es más sencillo pensar:

```text
Primero:
buscar todos los DP- y FP-
→ PERSONALES

Después:
buscar todos los HL-
→ FEDERAL
```

Esto hace el BAT más directo y fácil de mantener.

---

# 47. Los comodines son la clave

Estos patrones:

```text
DP-*.tif
FP-*.tif
HL-*.tif
```

son extremadamente importantes.

El:

```text
*
```

significa:

> "Después del prefijo puede venir cualquier cosa."

Por ejemplo:

```text
DP-01.tif
DP-02.tif
DP-100.tif
DP-A.tif
DP-DOCUMENTO.tif
```

todos coinciden con:

```text
DP-*.tif
```

El BAT no analiza si después viene `01`, `02`, `999` o texto.

Solamente le importa:

```text
empieza con DP-
y termina con .tif
```

---

# 48. Por qué `DP01.tif` NO se mueve

Nuestro patrón es:

```text
DP-*.tif
```

Por tanto:

```text
DP-01.tif
```

sí coincide.

Pero:

```text
DP01.tif
```

no coincide, porque falta:

```text
-
```

Tampoco coincidiría:

```text
DP_01.tif
```

porque utiliza `_` en vez de `-`.

Esto es intencional: establecimos como estándar:

```text
DP-
FP-
HL-
```

---

# 49. El resumen final

El BAT imprime:

```bat
echo Movidos a PERSONALES: %PERSONAL%
echo Movidos a FEDERAL   : %FED%
echo Conflictos          : %CONFLICTOS%
```

Si durante la ejecución ocurrieron:

```text
3 archivos DP/FP
2 archivos HL
1 conflicto
```

podrías obtener:

```text
Movidos a PERSONALES: 3
Movidos a FEDERAL   : 2
Conflictos          : 1
```

Esto es posible gracias a los contadores que iniciamos en cero y aumentamos durante los bucles.

---

# 50. Comprobación final de TIFF sueltos

Al terminar, el BAT vuelve a ejecutar:

```bat
dir /b /a-d "*.tif" 2^>nul
dir /b /a-d "*.tiff" 2^>nul
```

Esta es una idea importante.

Al principio preguntamos:

> "¿Qué TIFF existen?"

Después hacemos los movimientos.

Al final preguntamos:

> "¿Qué TIFF siguen aquí?"

Si no aparece ninguno:

```text
TIFF que quedaron sueltos en la carpeta ESCANER:
------------------------------------------------------------
------------------------------------------------------------
```

entonces los TIFF que coincidían con las reglas ya fueron organizados.

Si aparece:

```text
DP01.tif
```

puedes detectar inmediatamente que quedó fuera.

---

# 51. `pause`

```bat
pause
```

Detiene la ventana y normalmente muestra:

```text
Presione una tecla para continuar . . .
```

Esto es especialmente útil cuando ejecutas el BAT con doble clic.

Sin `pause`, la ventana podría cerrarse inmediatamente y no alcanzarías a leer el resumen.

---

# 52. `goto FIN`

```bat
goto FIN
```

Después de terminar correctamente, el BAT salta hasta:

```bat
:FIN
```

Esto es importante porque debajo se encuentra:

```bat
:ERROR_CARPETA
```

Si no hiciéramos el salto, Windows podría continuar leyendo las siguientes líneas y entrar accidentalmente en la sección de error.

Por tanto:

```bat
goto FIN
```

significa:

> "El trabajo normal ya terminó. Salta la sección de error y ve al final."

---

# 53. `endlocal`

Al final:

```bat
:FIN
endlocal
```

`endlocal` cierra el entorno abierto por:

```bat
setlocal
```

Es decir:

```text
setlocal
   ↓
variables privadas del BAT
   ↓
programa
   ↓
endlocal
   ↓
limpieza
```

---

# 54. El programa entero convertido a lenguaje humano

Ahora olvidemos la sintaxis.

El BAT, explicado como instrucciones humanas, dice aproximadamente esto:

```text
1. No muestres todas mis órdenes internas en pantalla.

2. Crea un entorno privado de trabajo.

3. Ve a la carpeta donde está guardado este BAT.

4. Cambia el título de la ventana.

5. Pregunta al usuario cuál es la CURP.

6. Si no escribió nada:
      mostrar error
      volver a preguntar.

7. Quita espacios de la CURP.

8. Si tiene menos de 18 caracteres:
      mostrar error
      volver a preguntar.

9. Si tiene más de 18 caracteres:
      mostrar error
      volver a preguntar.

10. Construye estas tres rutas:
      CURP
      CURP\PERSONALES
      CURP\FEDERAL

11. Si no existen:
      créalas.

12. Si no se pueden crear:
      detener el proceso.

13. Mostrar los TIFF que actualmente están en escaner.

14. Poner los contadores en cero.

15. Buscar todos:
      DP-*.tif
      DP-*.tiff
      FP-*.tif
      FP-*.tiff

16. Para cada archivo encontrado:
      comprobar que exista.

17. Si ya existe un archivo con el mismo nombre en PERSONALES:
      no moverlo
      registrar un conflicto.

18. Si no existe:
      moverlo a PERSONALES.

19. Si el movimiento funcionó:
      sumar uno al contador PERSONALES.

20. Buscar todos:
      HL-*.tif
      HL-*.tiff

21. Repetir la misma lógica,
      pero utilizando FEDERAL.

22. Mostrar cuántos archivos fueron movidos.

23. Volver a listar los TIFF que siguen sueltos.

24. Esperar a que el usuario presione una tecla.

25. Limpiar las variables y terminar.
```

---

# 55. Diagrama mental del BAT

Puedes memorizarlo como cinco grandes bloques:

```text
┌──────────────────────────┐
│ 1. PREPARAR ENTORNO      │
│ cd /d "%~dp0"            │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ 2. PEDIR Y VALIDAR CURP  │
│ set /p + if + goto       │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ 3. CREAR CARPETAS        │
│ md                       │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ 4. MOVER TIFF            │
│ for + if + move          │
│ DP/FP → PERSONALES       │
│ HL    → FEDERAL          │
└────────────┬─────────────┘
             ↓
┌──────────────────────────┐
│ 5. VERIFICAR RESULTADO   │
│ contadores + dir + pause │
└──────────────────────────┘
```

Si entiendes estos cinco bloques, ya entiendes la arquitectura del BAT.

---

# 56. Las instrucciones que más te conviene aprender

No necesitas memorizar todo inmediatamente.

Para empezar, concentraría el estudio en estas instrucciones:

| Instrucción | Idea que debes recordar |
|---|---|
| `echo` | mostrar texto |
| `set` | crear una variable |
| `set /p` | pedir datos al usuario |
| `%VARIABLE%` | leer una variable |
| `if` | tomar una decisión |
| `else` | hacer lo contrario si el `if` no se cumple |
| `goto` | saltar a otra parte |
| `:ETIQUETA` | lugar al que puede saltar `goto` |
| `md` | crear carpeta |
| `dir` | listar archivos |
| `move` | mover archivo |
| `for` | repetir una operación |
| `*` | cualquier texto |
| `errorlevel` | comprobar si un comando falló |
| `pause` | esperar una tecla |

Con eso ya puedes leer una parte considerable del programa.

---

# 57. Concepto fundamental: variable

Una variable es una caja con nombre.

Ejemplo:

```bat
set "NOMBRE=Victor"
```

Mentalmente:

```text
┌───────────────┐
│ NOMBRE        │
│---------------│
│ Victor        │
└───────────────┘
```

Cuando escribes:

```bat
echo %NOMBRE%
```

Windows abre la caja y obtiene:

```text
Victor
```

En nuestro BAT:

```text
CURP
DESTINO
PERSONALES
FEDERAL
PERSONAL
FED
CONFLICTOS
```

son todas cajas con información.

---

# 58. Concepto fundamental: condición

Una condición es una pregunta que solamente puede responder:

```text
Sí
```

o:

```text
No
```

Ejemplo:

```bat
if exist "DP-01.tif"
```

Pregunta:

```text
¿Existe DP-01.tif?
```

Otro:

```bat
if not defined CURP
```

Pregunta:

```text
¿CURP está vacía?
```

Programar consiste muchas veces en construir preguntas y decidir qué hacer según la respuesta.

---

# 59. Concepto fundamental: bucle

Un bucle evita repetir manualmente código.

Sin `for`, para 100 archivos tendríamos que escribir algo como:

```text
mover archivo 1
mover archivo 2
mover archivo 3
...
mover archivo 100
```

Con:

```bat
for
```

decimos:

> "Haz estas mismas instrucciones para todos los archivos encontrados."

Esta es una de las ideas más importantes de la programación.

---

# 60. Ejemplo paso a paso con cuatro archivos

Supongamos:

```text
DP-01.tif
DP-02.tif
FP-01.tif
HL-01.tif
```

CURP:

```text
TESTA000000AAAAA01
```

## Paso 1

Se crean variables:

```text
DESTINO =
C:\escaner\TESTA000000AAAAA01
```

```text
PERSONALES =
C:\escaner\TESTA000000AAAAA01\PERSONALES
```

```text
FEDERAL =
C:\escaner\TESTA000000AAAAA01\FEDERAL
```

## Paso 2

Se crean carpetas.

## Paso 3

Primer `for` encuentra:

```text
DP-01.tif
DP-02.tif
FP-01.tif
```

### Vuelta 1

```text
%%F = DP-01.tif
```

¿Existe?

```text
Sí
```

¿Ya existe en PERSONALES?

```text
No
```

Mover.

Contador:

```text
PERSONAL = 1
```

### Vuelta 2

```text
%%F = DP-02.tif
```

Mover.

```text
PERSONAL = 2
```

### Vuelta 3

```text
%%F = FP-01.tif
```

Mover.

```text
PERSONAL = 3
```

## Paso 4

Segundo `for` encuentra:

```text
HL-01.tif
```

Mover.

```text
FED = 1
```

## Resultado

```text
PERSONAL = 3
FED = 1
CONFLICTOS = 0
```

---

# 61. Ejemplo de conflicto

Supongamos que ya existe:

```text
TESTA000000AAAAA01\PERSONALES\DP-01.tif
```

y además sigue suelto:

```text
escaner\DP-01.tif
```

Cuando el BAT procesa el segundo:

```bat
if exist "%PERSONALES%\%%~nxF"
```

la respuesta será:

```text
Sí, ya existe.
```

Entonces:

```text
[CONFLICTO] DP-01.tif ya existe en PERSONALES. No se movio.
```

El archivo suelto permanece donde está.

Esto evita que el BAT destruya silenciosamente el archivo que ya estaba archivado.

---

# 62. Algo importante sobre los nombres

Este BAT depende de una **convención de nombres**.

Eso significa que el nombre del TIFF contiene información que el programa utiliza para decidir.

Nuestro pequeño lenguaje es:

```text
DP- = PERSONAL
FP- = PERSONAL
HL- = FEDERAL
```

El nombre del archivo deja de ser solamente una descripción.

También funciona como un **dato estructurado** que el programa interpreta.

Ese concepto es muy importante en automatización documental.

---

# 63. ¿Qué parte del trabajo sigue siendo manual?

Actualmente tú sigues determinando qué tipo de documento es y renombrando el TIFF.

Es decir:

```text
Documento escaneado
       ↓
humano identifica tipo
       ↓
humano asigna DP-, FP- o HL-
       ↓
BAT interpreta ese código
       ↓
BAT organiza automáticamente
```

El BAT no mira el contenido de la imagen TIFF.

Solamente interpreta el nombre.

---

# 64. ¿Qué parte ya está automatizada?

A partir del prefijo, el BAT sí automatiza:

- captura de CURP;
- creación de estructura;
- creación de `PERSONALES`;
- creación de `FEDERAL`;
- búsqueda de TIFF;
- clasificación por prefijo;
- movimiento;
- protección contra duplicados;
- conteo;
- verificación final.

Eso significa que convertiste varias decisiones repetitivas en reglas explícitas.

---

# 65. Cómo modificarías una regla en el futuro

Supongamos, solamente como ejercicio, que apareciera un prefijo nuevo:

```text
XX-
```

y quisieras que también fuera a PERSONALES.

Actualmente tenemos:

```bat
for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff") do (
```

Conceptualmente añadirías:

```text
XX-*.tif
XX-*.tiff
```

y quedaría:

```bat
for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff" "XX-*.tif" "XX-*.tiff") do (
```

No necesitas hacerlo ahora.

El ejemplo sirve para entender cómo la regla está expresada directamente en el patrón del `for`.

---

# 66. Cómo cambiarías el nombre de una carpeta

Actualmente:

```bat
set "PERSONALES=%DESTINO%\PERSONALES"
```

Si algún día la carpeta tuviera que llamarse:

```text
DOCUMENTOS_PERSONALES
```

la línea sería conceptualmente:

```bat
set "PERSONALES=%DESTINO%\DOCUMENTOS_PERSONALES"
```

El resto del código seguiría utilizando la variable `%PERSONALES%`.

Esto demuestra una ventaja de las variables:

no tienes que escribir la ruta completa en 20 lugares.

---

# 67. Por qué las variables hacen más mantenible el programa

Imagina que no tuviéramos:

```bat
set "PERSONALES=%DESTINO%\PERSONALES"
```

Tendríamos que repetir muchas veces:

```text
C:\escaner\CURP\PERSONALES
```

Si el nombre cambiara, tendríamos que corregirlo en todos lados.

Con una variable:

```text
PERSONALES
```

definimos la ruta una vez y luego la reutilizamos.

Ese principio aparece en prácticamente todos los lenguajes de programación.

---

# 68. Tres tipos de errores que el BAT intenta controlar

## 1. Error del usuario

Ejemplo:

```text
CURP vacía
```

Respuesta:

```text
volver a pedirla
```

## 2. Error estructural

Ejemplo:

```text
no se puede crear una carpeta
```

Respuesta:

```text
detener el proceso
```

## 3. Conflicto de datos

Ejemplo:

```text
DP-01.tif ya existe en PERSONALES
```

Respuesta:

```text
no reemplazarlo
registrar conflicto
```

Esta separación es buena para entender cómo se diseña una automatización confiable.

---

# 69. Lo que significa "robusto" en este BAT

En este contexto, robusto no significa que sea imposible que falle.

Significa que el programa intenta comportarse de forma predecible ante situaciones comunes.

Por ejemplo:

- fija su carpeta de trabajo;
- usa comillas en las rutas;
- valida que la CURP no esté vacía;
- valida la longitud;
- comprueba creación de carpetas;
- comprueba existencia de archivos;
- evita duplicados;
- comprueba el resultado de `move`;
- muestra un diagnóstico final.

---

# 70. Cómo estudiaría yo este BAT siendo principiante

No intentaría memorizar las 100+ líneas.

Lo estudiaría en este orden:

## Nivel 1 — entender el flujo

Aprende primero:

```text
entrada
→ validación
→ carpetas
→ búsqueda
→ movimiento
→ resumen
```

## Nivel 2 — aprender 8 comandos

```text
echo
set
if
goto
md
dir
for
move
```

## Nivel 3 — entender variables

```text
%CURP%
%DESTINO%
%PERSONALES%
```

## Nivel 4 — entender el `for`

```text
%%F
%%~fF
%%~nxF
```

## Nivel 5 — entender detalles avanzados

```text
%~dp0
errorlevel
2^>nul
>nul
^
```

Ese orden evita comenzar por las partes más raras del lenguaje Batch.

---

# 71. Ejercicio 1

Sin ejecutar nada, responde mentalmente:

Si:

```text
CURP = ABCD123456ABCDEFGH
```

y:

```text
CD = C:\escaner
```

¿qué contendrá?

```text
DESTINO
PERSONALES
FEDERAL
```

La idea es practicar sustitución de variables.

---

# 72. Ejercicio 2

Dado:

```text
DP-01.tif
FP-03.tif
HL-09.tif
OTRO.tif
```

pregúntate:

```text
¿Qué archivos entran en el primer for?
¿Qué archivos entran en el segundo for?
¿Qué archivo quedará suelto?
```

Respuesta:

```text
Primer for:
DP-01.tif
FP-03.tif

Segundo for:
HL-09.tif

Quedará suelto:
OTRO.tif
```

---

# 73. Ejercicio 3

¿Qué ocurre con:

```text
DP01.tif
```

Respuesta:

No coincide con:

```text
DP-*.tif
```

porque falta el guion.

Por tanto permanecerá suelto.

---

# 74. Ejercicio 4

¿Qué ocurre si existen:

```text
escaner\DP-01.tif
```

y:

```text
CURP\PERSONALES\DP-01.tif
```

Respuesta:

El BAT detecta conflicto y no mueve el archivo suelto.

---

# 75. Ejercicio 5

Intenta explicar tú mismo esta línea sin mirar la respuesta:

```bat
move /Y "%%~fF" "%PERSONALES%\" >nul
```

Una buena explicación sería:

> Toma el archivo actual que está procesando el `for`, utiliza su ruta completa, muévelo a la carpeta PERSONALES y oculta el mensaje normal que genera el comando `move`.

Si puedes explicar esa línea, ya estás entendiendo una parte muy importante del programa.

---

# 76. Mini diccionario Batch de este proyecto

```text
@echo off
    No mostrar cada comando mientras se ejecuta.

rem
    Comentario.

set
    Crear o modificar una variable.

set /p
    Pedir información al usuario.

set /a
    Hacer operaciones numéricas.

%VARIABLE%
    Obtener el contenido de una variable.

if
    Ejecutar algo solamente si una condición se cumple.

else
    Ejecutar otra cosa si la condición no se cumplió.

exist
    Comprobar que un archivo o carpeta existe.

defined
    Comprobar si una variable tiene contenido.

goto
    Saltar a otra sección.

:ETIQUETA
    Crear un punto al que puede saltar goto.

cd
    Cambiar carpeta de trabajo.

md
    Crear carpeta.

dir
    Mostrar archivos.

for
    Repetir instrucciones para múltiples elementos.

move
    Mover archivos.

errorlevel
    Revisar el código de resultado del comando anterior.

pause
    Esperar a que el usuario presione una tecla.

setlocal
    Empezar un entorno local de variables.

endlocal
    Terminar ese entorno.

*
    Comodín: cualquier secuencia de caracteres.

>
    Redirección de salida.

nul
    Destino especial que descarta lo que recibe.

^
    Carácter de escape de CMD.
```

---

# 77. Las cinco líneas que quiero que puedas explicar de memoria

Cuando hayas estudiado el documento, intenta explicar estas cinco:

```bat
cd /d "%~dp0"
```

```bat
set /p "CURP=Ingrese la CURP del expediente: "
```

```bat
set "PERSONALES=%DESTINO%\PERSONALES"
```

```bat
for %%F in ("DP-*.tif" "DP-*.tiff" "FP-*.tif" "FP-*.tiff") do (
```

```bat
move /Y "%%~fF" "%PERSONALES%\" >nul
```

Si entiendes esas cinco, ya comprendes el corazón del programa.

---

# 78. Qué conocimientos de programación estás practicando realmente

Aunque el archivo sea un BAT relativamente pequeño, contiene varios fundamentos reales de programación:

## Entrada

```bat
set /p
```

El programa recibe información.

## Variables

```bat
CURP
DESTINO
PERSONALES
```

El programa conserva información.

## Condiciones

```bat
if
else
```

El programa toma decisiones.

## Bucles

```bat
for
```

El programa repite acciones.

## Manejo de errores

```bat
errorlevel
```

El programa comprueba resultados.

## Flujo de control

```bat
goto
```

El programa puede saltar entre secciones.

## Sistema de archivos

```bat
dir
md
move
```

El programa manipula carpetas y archivos.

Estos conceptos después aparecen de formas diferentes en Python, JavaScript, C#, Java y prácticamente cualquier otro lenguaje.

---

# 79. Relación con Python

Para que empieces a conectar conceptos:

Batch:

```bat
set "CURP=TESTA000000AAAAA01"
```

idea equivalente en Python:

```python
curp = "TESTA000000AAAAA01"
```

Batch:

```bat
if not defined CURP (
```

idea equivalente:

```python
if not curp:
```

Batch:

```bat
for %%F in (...) do (
```

idea equivalente:

```python
for archivo in archivos:
```

Batch:

```bat
set /a PERSONAL+=1
```

idea equivalente:

```python
personal += 1
```

No son traducciones exactas del programa, pero sí representan conceptos similares.

Esto es importante porque lo que aprendes aquí no se pierde si posteriormente automatizas el proceso con Python.

---

# 80. Qué deberías poder explicar después de estudiar esta guía

Tu objetivo no debería ser memorizar cada símbolo.

Deberías poder responder con tus propias palabras:

1. ¿Por qué el BAT utiliza `%~dp0`?
2. ¿Qué es una variable?
3. ¿Qué contiene `%CURP%`?
4. ¿Cómo se construye la ruta de `PERSONALES`?
5. ¿Qué hace `if`?
6. ¿Qué hace `for`?
7. ¿Qué significa el `*`?
8. ¿Qué representa `%%F`?
9. ¿Cuál es la diferencia entre `%%~fF` y `%%~nxF`?
10. ¿Qué comando mueve realmente el archivo?
11. ¿Cómo evita el programa sobrescribir un TIFF?
12. ¿Cómo sabe si `move` falló?
13. ¿Por qué hay dos bucles?
14. ¿Por qué `DP01.tif` no coincide con `DP-*.tif`?
15. ¿Para qué sirve el listado final de TIFF?

Si puedes explicar estas 15 respuestas sin copiar el texto, ya tienes una comprensión bastante buena de este BAT.

---

# 81. Resumen final en una sola frase

El BAT es básicamente:

> **un conjunto de variables, decisiones y bucles que convierte el prefijo del nombre de cada TIFF en una regla automática de organización dentro del expediente indicado por la CURP.**

Ese es el corazón del programa.

---

# 82. Siguiente nivel de estudio sugerido

Una vez que domines este BAT, los siguientes temas naturales serían:

1. escribir un BAT pequeño desde cero;
2. crear tus propias variables;
3. practicar `if`;
4. practicar comodines;
5. practicar `for`;
6. analizar errores con `errorlevel`;
7. pasar parámetros a un BAT;
8. posteriormente reproducir la misma automatización en Python.

No necesitas avanzar a Python para entender este archivo. Primero puedes dominar completamente esta versión y utilizarla como un pequeño laboratorio de programación real aplicado a tu trabajo.
