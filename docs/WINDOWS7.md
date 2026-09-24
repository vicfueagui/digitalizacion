# Aviso vigente del kit 0.6.3

Para trasladar el sistema a Windows 10 sigue [MIGRACION_WINDOWS10](../MIGRACION_WINDOWS10.html). No actualices producción solo para obtener las herramientas: abre MIGRAR.bat desde el kit separado. Programa 0.6.2, esquema7/TIFF3 y runtime3.8.10/Pillow9.5 se conservan durante el traslado. Los procedimientos históricos siguientes siguen siendo referencia de instalación/actualización tradicional, no sustituyen el traslado formal.

Los BAT actuales comparten EJECUTAR.bat y ejecutan una comprobación real del intérprete. Una .venv con python.exe de0 bytes se rechaza. Puede configurarse una ruta absoluta en python_ruta.txt; después se prueban alternativas compatibles instaladas. INSTALAR_VISOR.bat prepara un entorno local sin modificar paquetes globales. No copiar una .venv entre equipos. Evidencia y pendientes nativos: [VALIDACION_V063.md](VALIDACION_V063.md).

# Windows 7: actualización protegida de producción

**No se ha ejecutado esta entrega en el equipo de oficina.** Antes de producción, usa los pasos de ensayo. Los comandos siguientes son para **Símbolo del sistema (cmd.exe)**. Ajusta únicamente las rutas de ejemplo a las carpetas reales; no pegues rutas de otra instalación.

Objetivo legado: Windows 7 SP1 Professional x64, Python **3.8.10 de 64 bits**, Tcl/Tk y Pillow **9.5.0**. Conserva esos componentes en la oficina. El Mac usa otro perfil. El sistema y Python 3.8 están fuera de soporte; trabaja con archivos de procedencia controlada y evita exposición a red. No se propone instalar Docker.

## Recorrido recomendado con botones

Abre [ACTUALIZACION.html](../ACTUALIZACION.html): explica cada paso sin asumir experiencia técnica. Después de comprobar y extraer el ZIP, ejecuta **ACTUALIZAR.bat** desde el paquete nuevo. El asistente elige el proyecto existente, comprueba paquete/base/entorno, ejecuta el ensayo independiente con ventanas y permite abrir la demo. Tras revisión humana y cierre de aplicaciones, crea el respaldo y aplica mediante el mismo `actualizar.py`. No instala dependencias ni abre producción automáticamente. Usa `.venv\Scripts\python.exe` del destino en Windows y exige el perfil Windows 7 SP1 para el ensayo. Cambiar de destino o paquete invalida el ensayo previo.

Los apartados siguientes son la **alternativa por comandos**, preparación inicial y referencia para administración. Sigue un solo recorrido completo; no apliques dos veces la misma entrega.

## 1. Preparar el ensayo, sin tocar la carpeta de operación

Lleva `Digitalizacion-0.6.3-codigo.zip` y `Digitalizacion-0.6.3-codigo.sha256`. Antes de extraer, calcula:

```bat
certutil -hashfile "C:\Traslado\Digitalizacion-0.6.3-codigo.zip" SHA256
```

Compara con el archivo `.sha256`. El hash detecta alteraciones del traslado; verifica también la procedencia del paquete. Extrae el ZIP con el Explorador en `C:\ActualizacionDigitalizacion063`, fuera de la carpeta de producción.

En cmd.exe:

```bat
cd /d "C:\ActualizacionDigitalizacion063"
py -3.8 -c "import sys,struct; print(sys.version); print(struct.calcsize('P')*8); assert sys.version_info[:3]==(3,8,10) and struct.calcsize('P')==8"
py -3.8 -m venv .venv
.venv\Scripts\python.exe instalar_visor.py
.venv\Scripts\python.exe main.py --diagnostico
.venv\Scripts\python.exe -m tkinter
```

El primer comando debe indicar 3.8.10 y 64. Si no existe `py`, usa la ruta del Python ya instalado, por ejemplo `"C:\Python38\python.exe" -m venv .venv`; **ese ejemplo no determina dónde está tu Python**. El archivo local `python_ruta.txt`, si existe, sirve para consultar la ruta anterior. No instales otro Python global por ensayo y error.

`instalar_visor.py` comprueba Windows, CPython 3.8 x64, entorno virtual y SHA-256 del wheel incluido. Usa pip sin red y sin `--user`. No se requiere internet para Pillow. El instalador completo de Python no viene en el paquete: si falta Python/Tk, solicita esa instalación a quien administra el equipo antes de continuar.

```bat
.venv\Scripts\python.exe tools\ensayo_oficina.py --destino "C:\PruebasDigitalizacion\ensayo062" --ventanas
.venv\Scripts\python.exe main.py --workspace "C:\PruebasDigitalizacion\ensayo062\demo"
```

La carpeta `ensayo062` no debe existir. El ensayo ejecuta la suite sintética, crea demo/respaldo/restauración y abre las ventanas automáticamente; guarda `resultado.json` y registros locales. Consulta [ENSAYO_OFICINA.md](ENSAYO_OFICINA.md) para interpretar los resultados. Nunca habilita las pruebas con fuentes privadas. Las ventanas automáticas se cierran; el segundo comando abre la demo para tu revisión.

Debes ver tres expedientes ficticios, dos legajos de la misma identidad, una incidencia y TIFF de una/tres páginas. Prueba Ctrl+15, Ctrl+120, Ctrl+Shift+100, teclado numérico español, zoom, recorte, cancelar, reescaneo, retirar/restaurar y organizar. Comprueba legibilidad y tiempos en los 3 GB de RAM. No uses el BAT organizador antiguo sobre estas mismas copias.

## 2. Preparar el Python del proyecto de oficina

Con el programa de oficina cerrado, crea su entorno local **sin copiar la .venv del Mac**. Ejemplo si la carpeta operativa real es `C:\Digitalizacion`:

```bat
cd /d "C:\Digitalizacion"
py -3.8 -m venv .venv
.venv\Scripts\python.exe "C:\ActualizacionDigitalizacion063\instalar_visor.py"
```

Si ya existe una `.venv` válida, no la vuelvas a crear: comprueba primero su versión con `.venv\Scripts\python.exe --version`. Los BAT nuevos usan `.venv\Scripts\python.exe`. El archivo `python_ruta.txt` se conserva pero ya no sustituye al entorno virtual.

## 3. Comprobar y aplicar la actualización

Cierra **todas** las versiones de la aplicación y cualquier herramienta que modifique sus TIFF. El bloqueo de la versión nueva no puede obligar a una versión vieja a cooperar. La carpeta de datos debe estar en disco local con soporte de enlaces de archivos, normalmente NTFS; no operes desde FAT/exFAT, unidades de red o una carpeta sincronizada.

```bat
cd /d "C:\ActualizacionDigitalizacion063"
.venv\Scripts\python.exe actualizar.py --destino "C:\Digitalizacion"
```

Resultado esperado: comprobación correcta y número de archivos, sin cambios en el destino. Si la base no está en `C:\Digitalizacion\datos\digitalizacion.sqlite3`, el actualizador se detiene: no adivina otra ubicación. Consulta primero [RESPALDOS.md](RESPALDOS.md) para instalaciones con rutas distintas.

Después de pasar el ensayo y la comprobación:

```bat
.venv\Scripts\python.exe actualizar.py --destino "C:\Digitalizacion" --aplicar
```

El actualizador:

1. Bloquea el espacio para otros procesos nuevos, lee SQLite mediante backup API y guarda base, documentos y reportes en una carpeta hermana `Digitalizacion_resguardo_FECHA_ID\datos_antes`.
2. Comprueba integridad y referencias TIFF, guarda el código anterior y prepara el nuevo.
3. Reemplaza exclusivamente la lista permitida de código; **no reemplaza datos, respaldos previos, reportes previos, fuentes, configuración local ni .venv**. Si falla una copia normal, intenta recuperar el código anterior tras comprobar que los datos siguen iguales. Si la recuperación falla, conserva la marca pendiente y muestra el error.
4. Deja `actualizacion.json` con el resultado. La base productiva sigue byte por byte como estaba antes de copiar el código. La migración ocurre al abrir el programa actualizado.

Debe haber espacio libre para el respaldo completo y el código. Si se corta la energía, `.actualizacion_pendiente.json` registra el resguardo y la versión nueva bloquea abrir el espacio. No borres esa marca para continuar y no abras una mezcla de código viejo/nuevo: usa el resguardo y el procedimiento de recuperación descrito abajo. No vuelvas a extraer el ZIP encima de datos.

## 4. Primer arranque controlado

Conserva el resguardo fuera del trabajo diario. Desde producción:

```bat
cd /d "C:\Digitalizacion"
DIAGNOSTICO.bat
INICIAR.bat
```

Diagnóstico solo lee. El arranque genera un snapshot SQLite previo si necesita migración, migra hasta núcleo 7 / TIFF 3 en una transacción y conserva IDs, historiales y archivos. Desde 0.6.0 no hay migración de esquema; 0.6.2 conserva núcleo 7 / TIFF 3. La migración desde 0.5.0 incorpora directorio y procedencia de listas, enlazando los nombres existentes sin reemplazar su texto histórico. Para versiones más antiguas, el nuevo modelo enlaza maestros, préstamos y ciclos; reconstruye la tabla TIFF para retirar la antigua unicidad por hash, comprobando sus relaciones. No se mueve ni elimina ningún documento durante esa migración. Una migración fallida revierte el esquema; una versión futura desconocida se rechaza. No hay fusión automática de duplicados.

Compara los expedientes, folios, dos legajos conocidos, incidencias, conteos y TIFF con el estado anterior. Revisa los vínculos históricos pendientes en Expediente 360 y confirma solo los que tengan evidencia; una migración no acredita recepción física ni fechas antiguas. Los registros históricos duplicados pueden mostrarse como una sola identidad: revisa Registros asociados, no borres filas para igualar un número de pantalla. Exporta un diagnóstico local si hace falta:

```bat
.venv\Scripts\python.exe main.py --duplicados
```

El CSV queda en `reportes\diagnostico_duplicados.csv` y contiene información local; no lo publiques. Realiza un respaldo completo desde **Importación y respaldo → Respaldar base y TIFF** antes de retomar la jornada.

## Si hay un fallo

Ante un error ordinario de copia, revisa el mensaje y `actualizacion.json`; el actualizador intenta recuperar el código anterior. Si hubo corte de energía o falla al revertir, conserva la carpeta completa y no continúes operando en ella.

Desde el paquete 0.6.2 extraído, con todas las aplicaciones cerradas, puedes recuperar **solo código**. Sustituye `FECHA_ID` por el nombre exacto del resguardo indicado en el mensaje o en `.actualizacion_pendiente.json`:

```bat
cd /d "C:\ActualizacionDigitalizacion063"
.venv\Scripts\python.exe actualizar.py --destino "C:\Digitalizacion" --recuperar-codigo "C:\Digitalizacion_resguardo_FECHA_ID"
```

Este comando compara el contenido lógico de SQLite, incluidas transacciones confirmadas en WAL, y las huellas de documentos/reportes con el estado previo. Solo restituye archivos de código reconocidos y elimina archivos añadidos por esa actualización. No restaura ni escribe SQLite o TIFF. También rechaza código anterior dañado, ediciones manuales posteriores y otro resguardo pendiente. Si se interrumpe, conserva la marca y puedes repetir el mismo comando cuando se resuelva el fallo.

**Si ya hubo migración o cambios en datos, la recuperación del código se detiene.** No quites la marca ni fuerces el retorno. Los resguardos de 0.4 no tienen la huella necesaria para este comando. Para esos casos, restaura `datos_antes` a **otra carpeta**, copia allí `codigo_antes` y crea su `.venv` con Python de Windows siguiendo [RESPALDOS.md](RESPALDOS.md). Valida esa copia antes de decidir cuál será productiva. No pongas código antiguo sobre una base que ya migró.

Si ya hubo nueva captura después de actualizar, no restaures encima el respaldo previo: perderías esa captura. Guarda ambos estados y solicita conciliación autorizada. Git y la sincronización bidireccional no resuelven conflictos SQLite ni TIFF.

El cumplimiento de estos pasos debe registrarse por el operador de oficina. La validación macOS y la gramática Python 3.8 no equivalen a una certificación de Windows 7.

## Comprobaciones específicas de 0.6.2

Sigue [RECEPCION_INDICADORES_V061.md](RECEPCION_INDICADORES_V061.md): acepta varios elementos sin recapturar CURP, cancela otra selección, confirma que repetir no duplica y revisa las cifras de barras con cero/resultados filtrados. Comprueba escala y contraste reales de Windows.

Prueba [IMPORTACION_FOLIOS_V06.md](IMPORTACION_FOLIOS_V06.md) con `demo\ejemplos\lista_folio_sintetica.csv`: encabezados, legajos pendientes, desglose 1/2/3, catálogos y búsqueda al escribir. Repetir el archivo no debe duplicar los elementos. Verifica que los TIFF y páginas pertenezcan solo al legajo seleccionado.

Sigue también el [manual vigente](MANUAL_USUARIO.html): recepción parcial, asignación, 360, entregas v1/v2, observación, validación, aprobación y devolución física independiente. En Codificación comprueba Detalles, Lista y Miniaturas, Ctrl + rueda para tamaño y rueda para desplazamiento. Arrastra los separadores; los menús Archivo/Editar/Vista conservan las herramientas menos frecuentes. La vista central usa la rueda para zoom y Shift + rueda para desplazar. Revisa a la resolución y escalado reales del equipo.

Se corrigió el respaldo en Windows: `-wal`, `-shm` y `-journal` se excluyen antes de llamar a `plain_path` o consultar sus atributos, porque el sistema puede mantenerlos bloqueados. La base se sigue obteniendo con la API de SQLite. No se omiten pruebas ni se ignoran globalmente errores de acceso. Comprueba en el informe que `test_wal_committed_data_also_blocks_recovery` y `test_backup_wal_and_corruption_refused` pasen; hay regresiones adicionales que simulan auxiliares bloqueados y conservan el fallo ante un archivo incluido inaccesible.

Los resultados realizados en Mac y lo pendiente están en [VALIDACION_V062.md](VALIDACION_V062.md). La corrección se comprobó localmente y mediante simulación; su ejecución real en Windows 7 debe registrarse en el ensayo de este equipo.
