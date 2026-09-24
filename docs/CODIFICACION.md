> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

> Documento histórico v0.2. La versión 0.3 cambia identidad, atajos, correcciones y visor: consulta CAMBIOS_V03.md.

# Codificación y visor TIFF — versión 0.2

## Flujo

En Expedientes selecciona un trabajo y pulsa Codificar TIFF. El título muestra folio, CURP y legajo: verifica esa identidad antes de importar escaneos. Solo puede estar abierta una ventana de codificación a la vez.

Importar TIFF permite elegir varios archivos; Importar carpeta incluye los TIFF directamente dentro de la carpeta, sin recorrer subcarpetas. El programa crea una copia original inmutable por convención y otra de trabajo; no modifica los archivos externos seleccionados. Detecta duplicados idénticos por SHA-256 dentro del mismo trabajo. Un mismo archivo puede importarse en otro legajo solo mediante una selección explícita para ese trabajo.

No se incluyen escaneos reales de ejemplo en la actualización. Ensaya primero con copias de dos o tres TIFF, incluyendo uno multipágina.

## Almacenamiento

Cada trabajo tiene una carpeta independiente:

- datos/tiff/trabajo_ID/originales: respaldo íntegro de cada archivo importado.
- datos/tiff/trabajo_ID/entrada: copias en proceso de codificación.
- datos/tiff/trabajo_ID/revisiones: versiones anteriores a ediciones guardadas.
- datos/tiff/trabajo_ID/CURP/PERSONALES y FEDERAL: salida organizada.
- datos/tiff/trabajo_ID/recuperados: copias no registradas recuperadas tras una interrupción, cuando corresponda.

El ID interno separa incluso dos trabajos de la misma CURP en distintos folios. Dentro de cada entrega se conserva la estructura CURP/PERSONALES/FEDERAL. Al entregar dos legajos, identifica también la carpeta exterior por folio/legajo; no fusiones ambas carpetas CURP sin conservar esa separación.

El respaldo SQLite de la v0.1 no contiene las imágenes. Para respaldar todo el nuevo trabajo, cierra la aplicación y copia la carpeta datos completa, además de tus fuentes. Una copia de digitalizacion.sqlite3 por sí sola ya no basta para restaurar los archivos TIFF.

## Explorador y navegación

Lista con nombre, cantidad de páginas, fecha/hora del escaneo, código y estado. Se puede ordenar por fecha de modificación original, fecha de creación original, nombre o código, ascendente/descendente. Las fechas se capturan al importar y permanecen estables aunque se renombre o edite. En Windows, creación usa el dato del sistema de archivos; no demuestra cuándo se escaneó el documento.

F7/F8 cambian de archivo; RePág/AvPág cambian de página dentro del TIFF. También hay botones. Renombrar el TIFF cambia el nombre del archivo completo, no el de una página. Esta versión no divide ni une TIFF multipágina: si un TIFF contiene documentos de distintos códigos, debe separarse antes de asignarle un único código.

## Atajos

Se asigna automáticamente una secuencia única a cada código activo. F6 activa el modo de código; después se pulsan dos letras sucesivas, sin mantenerlas juntas. Escape cancela. Las 64 asignaciones iniciales están en ATAJOS_DOCUMENTOS.md; la lista dentro de la aplicación es la autoridad si el catálogo cambió.

Para los primeros nueve códigos del catálogo inicial también se proponen Ctrl+1 a Ctrl+9. Atajos permite cambiar secuencia y favorito; no se permiten colisiones. Los nuevos códigos reciben una secuencia disponible sin cambiar las existentes. Los códigos desactivados conservan su reserva para evitar reasignar silenciosamente un hábito de teclado.

Los atajos funcionan únicamente en la ventana de codificación y no se aplican al escribir en campos de texto. No registran teclas globales en Windows. Puedes buscar el catálogo por código/título/descripción y asignar mediante doble clic o botón. Cada asignación renombra automáticamente y, si la opción está marcada, pasa al archivo siguiente. El orden previo de la lista determina cuál es el siguiente.

F2 abre renombrado manual. Nombres admitidos: código activo de dos dígitos más sufijo opcional y extensión .tif/.tiff. Por ejemplo DP-01.tif, DP-01 (2).tif o DP-01 NOTA.tif. La asignación automática reserva nombres en todo el trabajo y agrega (2), (3)… cuando es necesario. No se sobrescriben archivos existentes.

## Visor y edición

Ajustar muestra la página completa. +/−, 100% o Ctrl+rueda controlan zoom. La rueda desplaza verticalmente; arrastrar desplaza la imagen cuando no está activo el recorte. Las barras permiten recorrer imágenes grandes.

Edición de la página actual: giro de 90°, ajustes de ±0.2°, ángulo personalizado y recorte con arrastre. El recorte muestra un rectángulo y al soltar aparece su vista previa. Deshacer/Ctrl+Z retira el último ajuste no guardado. Descartar elimina todos los ajustes pendientes. Ver sin cambios permite comparar con la versión guardada actual; no confundir con el escaneo original de importación.

Guardar/Ctrl+S aplica los ajustes sobre la copia de trabajo. Antes se guarda una revisión, se reescribe el TIFF página por página, y se verifica número de páginas y píxeles de todas ellas. Se conserva DPI y un conjunto de etiquetas descriptivas y perfil ICC cuando existe. No se promete conservar todas las etiquetas privadas del escáner: el original conserva sus bytes intactos. Se usa compresión TIFF Deflate sin pérdida. La rotación fina interpola píxeles; una página binaria puede pasar a escala de grises para conservar suavidad del texto.

Cambiar de archivo, página, codificar o cerrar con ajustes pendientes pregunta Guardar / Descartar / Cancelar. Historial / originales muestra operaciones y permite restaurar todas las páginas del original, conservando el nombre codificado y respaldando la versión sustituida.

La pantalla limita el render a 16 millones de píxeles y la página fuente a 36 millones, para acotar memoria en el equipo de 3 GB. Procesa una página a la vez; un TIFF multipágina grande aún puede tardar al validar/guardar. No está implementada cancelación durante la escritura: espera a que termine. Las ediciones se hacen en copias y con archivos temporales antes del reemplazo.

## Organización y reportes

Organizar y generar reporte muestra primero la lista de origen/destino. Al confirmar crea PERSONALES/FEDERAL en la carpeta de este trabajo y mueve las copias codificadas. Cumple la función del BAT desde la aplicación, pero no lanza el BAT heredado: ese script no distingue legajos. La aplicación consulta la carpeta del catálogo; inicialmente DP/FP → PERSONALES y HL → FEDERAL.

Se bloquea la organización si hay archivos sin código activo, colisiones, cambios externos, TIFF ilegibles, archivos desconocidos en destino o total físico sin confirmar. No se revisan otras carpetas de escaneo de Windows ni se declara que esas carpetas externas estén vacías.

Cada ejecución exitosa genera archivos.csv e inventario.csv en reportes y un inventario vinculado al trabajo/legajo en la base. Contiene individuales, multi y páginas por carpeta y sus totales. Repetir la organización no duplica el inventario en KPI. La versión de origen aparece como APP_0.2, no como BAT 3.1.

inventario.csv incluye las 66 métricas más FOLIO, LEGAJO, TRABAJO_ID, ALCANCE e ID_EJECUCION: no se debe pasar al importador heredado de CSV de 66 columnas, porque ya quedó registrado automáticamente. El CSV central C:\Reportes del BAT se mantiene independiente. La aplicación no avanza automáticamente las etapas ni cierra expedientes por haber creado carpetas.

Editar, renombrar, restaurar o importar TIFF invalida los inventarios anteriores del trabajo y desmarca carpetas: vuelve a organizar para generar un inventario actualizado. Una organización parcial por error registra cada movimiento ya completado y puede reintentarse; no se genera reporte final hasta terminar todo.

## Interrupciones

Antes de una operación se registra una intención en operaciones_tiff; al terminar se marca Completada. Si el proceso se interrumpe entre escritura y registro final, se bloquean cambios del trabajo y se ofrece Recuperar operación. La recuperación intenta restablecer el último archivo conocido por su hash o conserva las importaciones huérfanas en recuperados. Si hay un conflicto no recuperable automáticamente, no sobrescribe ambos archivos; conserva la carpeta y solicita asistencia con el mensaje exacto.

La base y los archivos no forman una única transacción del sistema operativo. La estrategia es copias originales, revisiones, verificación, operaciones atómicas individuales y diario de intención. No se garantiza recuperación frente a daños físicos del disco: se requiere respaldo externo completo.

## Actualización de datos

Se agregan cuatro tablas (atajos, archivos_tiff, revisiones_tiff, operaciones_tiff) al abrir el módulo. Se conserva schema_version=1 para el núcleo y se registra coding_schema_version=1 para esta extensión aditiva. No se elimina ninguna tabla v0.1. Se respalda SQLite antes de la primera apertura del módulo.

## Dependencia y alcance probado

Pillow 9.5.0 tiene soporte declarado para Python 3.8 según https://pillow.readthedocs.io/en/stable/installation/python-support.html. Se incluye wheel de CPython 3.8 Windows x64 y su licencia, obtenido mediante pip download desde el índice de paquetes configurado. Su hash se verifica antes de instalar; no hace falta red para INSTALAR_VISOR.bat. No se afirma que la interfaz y ese binario hayan sido ejecutados en el Lanix.

Las pruebas de esta entrega corrieron con Python 3.12.14 y Pillow 12.3.0 en Linux. La sintaxis se comprobó contra Python 3.8. El entorno no permite verificar visualmente Tk ni ejecutar el wheel de Windows. Los resultados se detallan en VALIDACION_V02.md.
