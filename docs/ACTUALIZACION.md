# Actualizar Digitalización sin perder tus datos

**¿Vas a cambiar de computadora a Windows 10?** Usa [Migración Windows 10](../MIGRACION_WINDOWS10.html). Abre MIGRAR.bat del kit separado y conserva el código actual del origen. No apliques una actualización para poder trasladarte. Esta guía sigue siendo la operación independiente de actualizar código en una instalación tradicional. El destino dividido de una migración requiere un actualizador específico futuro; no selecciones su carpeta programa con este asistente.

**Versión que vas a instalar: 0.6.3.** Esta guía sirve para actualizar una instalación existente. El paquete lleva el programa y sus manuales; tus expedientes se quedan en su carpeta habitual. El asistente crea un respaldo completo antes de sustituir el código.

Si solo quieres aprender a trabajar, abre el [manual de uso con ejemplos](MANUAL_USUARIO.html). Para el procedimiento técnico alternativo está [WINDOWS7.md](WINDOWS7.md). Esta entrega se prepara con datos ficticios en Mac; las pruebas del equipo Windows 7 se hacen allí antes de actualizar producción.

## 1. Entender las tres carpetas

Imagina que tu programa es una libreta: actualizar cambia la herramienta con la que la lees, conservando lo que ya has anotado. Aun así, guardamos una copia de recuperación antes de empezar.

| Carpeta | Para qué sirve | Ejemplo de nombre |
| --- | --- | --- |
| Proyecto habitual | Contiene tu programa y tus datos reales. Aquí seguirás trabajando al terminar. | C:\Digitalizacion |
| Paquete nuevo extraído | Contiene la versión nueva y el asistente. Se guarda aparte del proyecto habitual. | C:\ActualizacionDigitalizacion063 |
| Pruebas | Aquí se crea una demo de ejemplo, con su respaldo y sus resultados. | C:\PruebasDigitalizacion |

**Estos nombres son ejemplos.** Usa las carpetas reales de tu equipo. No pegues el contenido del ZIP encima del proyecto habitual. No copies la carpeta completa del Mac ni su entorno `.venv` al equipo Windows.

Para encontrar tu proyecto habitual, haz clic derecho en el acceso que usas para abrir el sistema y consulta **Propiedades**. Busca la carpeta de destino. Dentro deben estar `main.py`, la carpeta `datos` y, dentro de esta, `digitalizacion.sqlite3`. El asistente comprobará esa ubicación. Si los datos están en otra carpeta por una configuración especial, consulta el apartado 11 antes de seguir.

## 2. Lo que necesitas antes de empezar

1. Reserva un momento sin capturas. Guarda lo que estés editando y cierra Digitalización y otros programas que modifiquen sus TIFF.
2. Conecta la laptop a la corriente. En la computadora de oficina, evita iniciar durante un corte programado.
3. Comprueba que el disco tenga espacio para una copia completa de los datos, los documentos y los archivos del programa. El resguardo se crea junto al proyecto habitual; si el disco está lleno, libera espacio fuera del archivo de expedientes o solicita apoyo.
4. Ten el ZIP de esta entrega y su archivo de comprobación: `Digitalizacion-0.6.3-codigo.zip` y `Digitalizacion-0.6.3-codigo.sha256`. El segundo contiene una huella, como un número de identificación del ZIP.
5. Conserva una copia reciente y verificada del respaldo completo en el medio autorizado por tu oficina. El resguardo de la actualización se guarda en el mismo disco y no sustituye una copia frente a una avería de ese disco.

El perfil previsto de oficina es **Windows 7 SP1 o Windows 10 de 64 bits, CPython 3.8.10 de 64 bits y Pillow 9.5.0**. Si el sistema ya funciona con ese perfil y tiene su `.venv` local, normalmente no necesitas reinstalar nada. La preparación inicial solo se hace si falta ese entorno; está al final de esta guía.

## 3. Comprobar que el ZIP llegó completo

1. Coloca el ZIP y el `.sha256` juntos; por ejemplo, en `C:\Traslado`.
2. Abre el `.sha256` con Bloc de notas. Verás una secuencia larga de letras y números seguida del nombre del ZIP.
3. Pulsa **Windows + R**, escribe `cmd` y pulsa Enter. Aparecerá una ventana de texto llamada Símbolo del sistema.
4. Escribe el comando siguiente cambiando la ruta si guardaste el ZIP en otro lugar. Conserva las comillas. Pulsa Enter.

```bat
certutil -hashfile "C:\Traslado\Digitalizacion-0.6.3-codigo.zip" SHA256
```

**Resultado esperado:** la secuencia que muestra la ventana coincide por completo con la del `.sha256`. Las mayúsculas y los espacios de presentación no cambian la huella. Si no coincide, vuelve a obtener el paquete; no continúes con esa copia. Recibe ambos archivos de la persona o canal que entrega el proyecto: la huella comprueba el traslado, no identifica por sí sola al remitente.

Después, haz clic derecho sobre el ZIP → **Extraer todo**. Elige una carpeta nueva, fuera del proyecto habitual, por ejemplo `C:\ActualizacionDigitalizacion063`. Entra hasta la carpeta que contiene `ACTUALIZAR.bat`, `actualizar.py`, `release-manifest.json` y este manual. No ejecutes el asistente dentro de la vista comprimida del ZIP.

## 4. Abrir el asistente y elegir el proyecto

1. Desde el paquete extraído, haz doble clic en **ACTUALIZAR.bat**.
2. Aparecerá **Actualizar Digitalización · 0.6.3**. Pulsa **1. Elegir proyecto…**.
3. Elige la carpeta del proyecto que usas a diario, por ejemplo `C:\Digitalizacion`. Elige la carpeta que contiene `main.py` y `datos`, no `datos` por separado.
4. Lee la ruta que quedó escrita en la ventana. Debe corresponder a tu proyecto habitual.
5. Pulsa **2. Comprobar paquete y proyecto**.

**Resultado esperado:** “Comprobación correcta”. Se revisan la huella de cada archivo del paquete, las rutas, la base y el Python del proyecto. Esta comprobación no modifica tus datos. Si eliges otra carpeta, se reinicia la comprobación y tendrás que repetir el ensayo.

El lanzador comprueba un intérprete real: .venv válida, python_ruta.txt y alternativas instaladas. Si .venv está vacía o rota no basta con que exista; configura la ruta de un Python compatible. Si el asistente no abre, consulta el apartado 10. Si señala un error, conserva el mensaje y ve al apartado 9. No hace falta ejecutar como administrador por rutina.

## 5. Probar la versión nueva con una demo

1. Pulsa **3. Probar en carpeta independiente…**.
2. Elige una carpeta de pruebas fuera del proyecto habitual y del paquete nuevo. Si no existe, créala con el botón de nueva carpeta del selector; por ejemplo `C:\PruebasDigitalizacion`.
3. Espera. El asistente crea una subcarpeta con fecha y un identificador, ejecuta las pruebas y abre y cierra ventanas de ejemplo. Esto puede tardar varios minutos en el equipo de oficina.
4. Cuando aparezca **Ensayo correcto**, pulsa **Abrir demo para revisarla**. La ventana principal debe indicar **DEMOSTRACIÓN FICTICIA**.
5. Comprueba que puedes leer los textos, abrir un expediente, ver sus TIFF, cambiar de página y usar las miniaturas. En **Indicadores**, revisa que se vean los números de las barras. Para practicar recepción utiliza el recorrido del manual, apartado 4.
6. Cierra la demo al terminar. Vuelve a la ventana del asistente.

**Resultado esperado:** pruebas automáticas correctas y demo utilizable en el equipo donde vas a trabajar. El informe `resultado.json` y los registros quedan en la carpeta del ensayo indicada en pantalla. Cada ensayo usa una carpeta distinta y se puede repetir sin borrar los anteriores.

En Windows el asistente exige que el informe corresponda a Windows 7 SP1, CPython 3.8.10 x64 y Pillow 9.5.0. En Mac permite ensayos locales y avisa de que no acreditan Windows. Ningún ensayo ficticio certifica por sí solo los datos reales de oficina. Si vienes de una versión anterior a 0.6.0 o existen datos históricos con dudas, realiza además la prueba con una copia restaurada que se describe en el apartado 11 antes de aplicar.

## 6. Crear el resguardo y actualizar

1. Confirma que la demo esté cerrada y que todos hayan dejado de trabajar con el proyecto habitual. Cierra también visores o editores externos que puedan cambiar sus archivos.
2. Marca la casilla **Revisé la demo, cerré su ventana y cerré el programa de trabajo…**.
3. Pulsa **4. Respaldar y actualizar el proyecto**.
4. La ventana mostrará de nuevo la carpeta que se actualizará. Comprueba la ruta y acepta solo si corresponde al proyecto habitual.
5. Espera hasta el mensaje de terminación. No cierres la ventana ni apagues el equipo durante la copia.

El programa vuelve a comprobar el paquete y crea una carpeta hermana con un nombre parecido a `Digitalizacion_resguardo_20260923_…`. Allí guarda `datos_antes` (base, TIFF y reportes gestionados), `codigo_antes` y el registro `actualizacion.json`. Luego sustituye únicamente los archivos de código autorizados. Conserva el entorno local, los datos de trabajo y los respaldos previos. Si detecta documentos faltantes o alterados, detiene la actualización para que se revise la causa.

**Resultado esperado:** **Actualización terminada**, con la ruta del resguardo y del registro `actualizacion.log`. Anota o copia esas rutas. Esta fase no migra la base; las migraciones compatibles, si hacen falta, ocurren al abrir el programa actualizado. Desde 0.6.0 y 0.6.1 se conserva el esquema núcleo 7 / TIFF 3.

## 7. Abrir y comprobar el proyecto actualizado

1. Cierra el asistente y regresa a la carpeta del proyecto habitual. No abras la demo por error.
2. Haz doble clic en **DIAGNOSTICO.bat**. Revisa que no reporte errores; para una base sana se espera **Integridad: ok**. El diagnóstico solo lee.
3. Haz doble clic en **INICIAR.bat**, en esa misma carpeta. El título debe mostrar **0.6.3**, sin “DEMOSTRACIÓN FICTICIA” si es tu instalación real.
4. Busca dos o tres expedientes que conozcas: compara CURP, folio, legajos, conteos y varias imágenes. Abre **Registros asociados** si un expediente tiene ciclos anteriores. Una sola fila de identidad puede reunir varios ciclos históricos; no elimines registros para igualar una cifra de pantalla.
5. Revisa **Folios**, una entrega anterior y sus observaciones. Comprueba que puedas abrir sus TIFF.
6. Abre **Ayuda**. Debe aparecer el manual local de uso.
7. En **Importación y respaldo**, pulsa **Respaldar base y TIFF**. Guarda la ruta que indique el sistema y verifica ese respaldo según el manual. Después puedes retomar la jornada.

Si aparece un error durante el primer arranque o la comparación, conserva los mensajes y detén nuevas capturas en esa instalación hasta revisarlo. No copies la base antigua sobre la nueva: podría haber cambios o capturas que deban conservarse.

## 8. Qué conservar al terminar y cómo repetir después

Conserva el ZIP y su `.sha256`, el resguardo completo, el informe del ensayo y la fecha de actualización. Registra quién actualizó, versión anterior y nueva, carpeta utilizada y qué expedientes verificó, en el registro interno autorizado. No publiques datos personales en la bitácora técnica del proyecto.

Para la siguiente entrega, repite los pasos con **su propio paquete, versión y huella**, en otra carpeta nueva. Abre siempre el asistente incluido en el paquete que quieres instalar. La primera preparación de Python no se repite si el entorno sigue siendo válido.

No borres de forma manual `datos`, `originales`, `versiones`, `entregas`, `reportes` ni manifiestos. El respaldo completo no recoge automáticamente los Excel/CSV fuente ni las carpetas externas solo analizadas: consérvalos por el procedimiento de archivo de tu oficina. Una carpeta de prueba se puede archivar aparte después de confirmar su contenido ficticio.

## 9. Si algo falla

| Lo que ves | Qué significa | Qué hacer |
| --- | --- | --- |
| No encuentra datos/digitalizacion.sqlite3 | Carpeta equivocada o instalación con datos en otra raíz. | Vuelve a elegir el proyecto; si usa otra raíz, revisa el apartado 11. No crees una base vacía para pasar el paso. |
| Hash distinto, archivo faltante o manifiesto inválido | El paquete está incompleto o fue cambiado. | Conserva el error y obtén otra copia del ZIP y su huella. Extrae en otra carpeta. |
| Proyecto abierto / bloqueo de instancia | Otra ventana mantiene el espacio en uso. | Guarda y cierra esa ventana. Si no hay ninguna, pide revisar el proceso; no borres el bloqueo a ciegas. |
| Python, Tk o Pillow incorrectos | Falta preparar el entorno local. | Sigue el apartado 10 o pide a quien administra el equipo que lo prepare. |
| Ensayo con error | Una comprobación automática falló. | Revisa resultado.json y el registro de la etapa. No continúes con producción; repite en carpeta nueva al resolver la causa. |
| Archivo TIFF faltante, alterado o enlace no admitido | No se puede obtener un respaldo íntegro. | Conserva la instalación y revisa esa referencia con el responsable. No omitas el archivo ni desactives la validación. |
| Acceso denegado o disco lleno | No se pudo leer o escribir un archivo necesario. | Cierra herramientas que lo usen y revisa espacio/permisos. El error indica el archivo; no desactives todas las protecciones. |
| Corte de energía / actualización pendiente | La operación quedó a medias. | Conserva la carpeta y el resguardo; usa la recuperación de código que sigue. No extraigas el ZIP encima ni borres la marca pendiente. |
| El retorno dice que los datos cambiaron | Hubo migración o nueva captura después del resguardo. | Conserva ambos estados y restaura a otra carpeta para comparar. No fuerces código antiguo sobre esa base. |

### Recuperar solo el código anterior

Este procedimiento es para quien acompaña la recuperación. Cierra todas las aplicaciones. Desde **cmd**, usa las rutas reales del proyecto, del paquete nuevo y del resguardo indicado por el error. `FECHA_ID` se sustituye por el nombre exacto; no se escribe literalmente.

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\actualizar.py" --destino "C:\Digitalizacion" --recuperar-codigo "C:\Digitalizacion_resguardo_FECHA_ID"
```

La recuperación comprueba que los datos sigan como estaban antes, incluyendo transacciones confirmadas de SQLite. Solo devuelve el código; no reemplaza la base ni los TIFF. Si hubo cambios de datos, se bloquea para evitar incompatibilidades. Si no puede recuperar, deja la marca pendiente y los registros para revisión.

Para recuperar datos, se restaura `datos_antes` a **una carpeta nueva** y se revisa allí. Si se pretende usar el código anterior, se coloca en esa nueva raíz el contenido de `codigo_antes`, conservando las rutas. Nunca se coloca un respaldo previo encima de capturas posteriores. Sigue [RESPALDOS.md](RESPALDOS.md) con quien administre el sistema.

## 10. Si no abre el asistente o falta la preparación inicial

**Si ya funciona el proyecto**, prueba iniciar el asistente con su propio Python. Pulsa Windows + R, escribe `cmd`, Enter y ejecuta, ajustando las rutas:

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\asistente_actualizacion.py"
```

Esto no abre la base: solo inicia la ventana del asistente. Si funciona, puedes continuar desde el paso 4. Evita reinstalar Python si ya existe el intérprete correcto. Si falta `.venv`, esta preparación se hace una vez, con el programa cerrado:

```bat
cd /d "C:\Digitalizacion"
py -3.8 -c "import sys,struct; print(sys.version); print(struct.calcsize('P')*8); assert sys.version_info[:3]==(3,8,10) and struct.calcsize('P')==8"
py -3.8 -m venv .venv
.venv\Scripts\python.exe "C:\ActualizacionDigitalizacion063\instalar_visor.py"
```

Ejecuta una línea por vez. La comprobación debe mostrar **3.8.10 y 64** y terminar sin error. Si falla, detente antes de crear el entorno. No vuelvas a crear una `.venv` existente por rutina. El instalador de Pillow utiliza el archivo incluido en el paquete, comprueba su huella y no necesita internet.

Si `py` no se reconoce, usa la ruta del Python 3.8.10 x64 que ya tenga el equipo, o pide instalar ese perfil con Tk a quien lo administra. El paquete no incluye el instalador completo de Python. En [WINDOWS7.md](WINDOWS7.md) está el procedimiento técnico y la alternativa por comandos. No copies la `.venv` del Mac: no es compatible con Windows.

## 11. Probar una copia real o usar una ubicación especial de datos

**Copia de verificación antes del primer uso:** con el programa cerrado, el código nuevo puede respaldar la instalación existente sin migrarla. Después verifica y restaura en una carpeta nueva. Las rutas son ejemplos y los destinos de respaldo/restauración no deben existir.

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\main.py" --workspace "C:\Digitalizacion" --respaldar "C:\PruebasDigitalizacion\respaldo-previo-062"
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\main.py" --verificar-respaldo "C:\PruebasDigitalizacion\respaldo-previo-062"
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\main.py" --restaurar "C:\PruebasDigitalizacion\respaldo-previo-062" --destino "C:\PruebasDigitalizacion\copia-062"
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\ActualizacionDigitalizacion063\main.py" --workspace "C:\PruebasDigitalizacion\copia-062"
```

Ejecuta una línea por vez y continúa solo si terminó correctamente. Abrir la copia puede migrar **esa copia**. Compara conteos, folios, legajos, historias e imágenes con el estado previo; ciérrala al terminar y vuelve al asistente. Esta copia contiene información real: debe quedarse en el medio y equipo autorizados. No será rotulada como demo, por eso comprueba cuidadosamente su ruta.

**Datos separados del código:** el asistente exige la instalación convencional, con `datos/digitalizacion.sqlite3` dentro del proyecto elegido. Si arrancas con `--workspace` en otra raíz, o con una base personalizada mediante `--db`, no elijas una carpeta distinta al azar ni muevas la base para engañar la comprobación. Usa el respaldo/restauración y revisión de una copia descritos en [RESPALDOS.md](RESPALDOS.md), identifica la raíz real y prepara con el administrador un traslado controlado. La actualización automática de esas disposiciones no está incluida.

## 12. Qué cambia en 0.6.3 y qué se ha comprobado

Esta entrega añade el asistente, el manual completo accesible desde **Ayuda** y esta guía. Conserva las funciones de recepción por selección, importación CSV/XLSX, varios legajos, directorio, Indicadores y visor TIFF. No cambia el esquema de 0.6.1 ni las reglas del respaldo.

El estado exacto de las pruebas está en [VALIDACION_V062.md](VALIDACION_V062.md). Se distingue lo ejecutado con datos ficticios en Mac de lo pendiente en Windows. El ensayo automático no sustituye la revisión humana de teclado, pantalla, impresión y rendimiento con documentos representativos del equipo de oficina.
