# Laptop: Mac Intel con Big Sur 11.7.11

Entorno detectado: x86_64, 16 GB RAM, Python 3.11.4, SQLite 3.42.0 y Tcl/Tk 8.6.12. Se creó `.venv` y se instaló Pillow 12.3.0, wheel CPython 3.11 `macosx_10_10_x86_64`, con libtiff. Tkinter y las ventanas de la aplicación se abrieron localmente. No se instaló software del sistema.

## Arranque ya preparado

Para probar **0.6.1**, abre en el Escritorio **Digitalizacion-Pruebas-OSX-061.command**. El laboratorio vive en `/Users/admin/PruebasDigitalizacionOSX`, con una copia independiente `codigo-0.6.1`. Permite continuar las demos de `sesiones-v06` o crear una nueva sin borrar las anteriores. Se conservan las copias y accesos 0.5.0/0.6.0; cierra la demo antes de abrirla desde otra versión.

Desde Terminal:

```sh
/bin/sh "/Users/admin/PruebasDigitalizacionOSX/Abrir-Pruebas-OSX-061.command"
```

Elige **Continuar prueba seleccionada**, **Crear y abrir prueba nueva** o **Comprobación automática**. Esta última crea otra carpeta en `ensayos-v061`; los registros están en `registros-v061`. El lanzador usa su propia `.venv`, código y datos: no abre el workspace del desarrollo. Cada demo nueva incluye `ejemplos/lista_folio_sintetica.csv`. Consulta [Recepción e indicadores](RECEPCION_INDICADORES_V061.md).

Para trabajar directamente con la demo de desarrollo 0.6.0:

Abre Terminal o la terminal integrada de Windsurf, pega:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python main.py --workspace ensayos/listas-v06-final/demo
```

Se abre la aplicación con datos ficticios. Selecciona el primer expediente y abre Codificar TIFF para recorrer sus imágenes. La demo permanece dentro de `ensayos/listas-v06-final/demo`; no toca la ubicación histórica `datos/` de la raíz del código.

Para recrear el entorno en otra copia de este mismo Mac, sin copiar `.venv`:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
python3 -m venv .venv
.venv/bin/python -m pip install --only-binary=:all: -r requirements-laptop.txt
.venv/bin/python -m pip check
.venv/bin/python main.py --diagnostico
.venv/bin/python -m tkinter
```

El diagnóstico no crea bases ni carpetas. La última orden abre la ventana de demostración de Tk; ciérrala después de verla. Una importación correcta de Tk no sustituye esta prueba. Si otra laptop carece de Tk, detente y pide a quien administra el equipo un intérprete compatible con Tcl/Tk. El instalador Windows incluido no sirve en Mac.

Crear una demo adicional (no repetir sobre una carpeta existente):

```sh
.venv/bin/python main.py --crear-demo demos/ensayo-2
/bin/sh iniciar.sh --workspace demos/ensayo-2
```

El generador rechaza cualquier destino existente, incluso vacío. Las identidades que genera son inventadas y solo satisfacen el formato de entrada; no se verifican en RENAPO.

## Windsurf

Abre la carpeta que contiene `main.py`. Si el editor dispone del selector de intérprete Python, elige `/Users/admin/Downloads/Digitalizacion/.venv/bin/python`. Si no aparece esa función, usa directamente los comandos completos de Terminal; no se requiere instalar una extensión para operar. No selecciones `/usr/bin/python`, que no es este entorno.

## Visor y teclado

- Rueda/trackpad sobre imagen: zoom con actualización diferida. Shift+rueda: desplazamiento vertical. Arrastrar sobre imagen: desplazar, salvo que esté activo Recortar. Barras permiten desplazamiento horizontal/vertical.
- Ajustar adapta la vista; 100% usa un píxel de imagen por unidad del canvas de Tk. La percepción final depende del escalado Retina del sistema; debe comprobarse manualmente en la pantalla concreta.
- F7/F8 cambian archivo; RePág/AvPág cambian página. Siempre se muestra la página actual.
- Archivos y Catálogo ocultan/muestran paneles; arrastra separadores. Restablecer paneles devuelve tamaños accesibles. F11 alterna solo imagen.
- Ctrl+Enter en una tabla muestra el texto completo de la fila. No modifica registros.
- Control numérico conserva el comportamiento de Windows. **Command no codifica**. Mantén Control, pulsa `1`, luego `5`, y suelta Control; no uses la tecla literal “15”. Para HL mantén además Shift hasta terminar los dígitos. Escape cancela. Cambiar los modificadores en mitad de una secuencia la cancela.
- Las reasignaciones por colisión de rangos aparecen en la tabla Atajos: consulta siempre esa tabla si amplías los códigos. La configuración admite 999 números por combinación; no crea códigos ausentes.

Las pruebas automáticas simulan foco, fila numérica y teclado numérico. La distribución española física, el trackpad y la ergonomía deben validarse manualmente: no se ha pulsado cada combinación en un teclado real de Windows 7.

## Pruebas

```sh
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/smoke_ui.py
```

La primera usa directorios temporales y fixtures sintéticos. Ocho pruebas históricas se omiten sin las fuentes privadas; hay pruebas adicionales de Excel y CSV inventados. La segunda abre y cierra ventanas con una demo temporal y comprueba que Cancelar conserva la edición. No necesita documentos reales.

No se recomienda Docker en este Mac: Big Sur queda fuera de los sistemas admitidos actualmente por Docker Desktop. Hay un cliente Docker 24.0.6 en el PATH; no demuestra que exista un motor operativo ni soporte vigente. No se inició Docker ni se añadió Dockerfile. `.dockerignore` permite solo código y pruebas por si se evalúa después en un equipo compatible.

## Codificación 0.5.0

La ventana prioriza los paneles Archivos, imagen y Catálogo. Las herramientas principales son compactas y se ajustan en filas al ancho disponible. Importar, Archivo, Editar y Vista agrupan el resto; Vista permite ocultar paneles, restablecerlos o consultar ayuda. Los separadores ajustan sus proporciones.

Archivos ofrece Detalles, Lista y Miniaturas de la primera página, con indicador de páginas por TIFF. Rueda desplaza; **Ctrl + rueda** aumenta/disminuye las miniaturas; también hay deslizador. La carga se limita a las celdas visibles y una caché acotada. El tamaño y modo se conservan al cerrar el visor. En la imagen central, rueda conserva zoom y Shift + rueda desplaza.
