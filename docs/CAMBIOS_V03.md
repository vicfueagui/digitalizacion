> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

# Versión 0.3 — expedientes, reescaneo y visor

Esta guía reemplaza las instrucciones de atajos con F6 y letras de versiones anteriores.

## Actualización

Cierra el programa, respalda la carpeta completa, extrae el ZIP aparte y copia su contenido dentro de tu proyecto actual, reemplazando código. No borres datos, fuentes ni tu Excel. Abre INICIAR.bat. Si ya instalaste el visor de v0.2 no necesitas instalarlo otra vez. El paquete conserva el instalador local para quien no lo haya instalado. No reimportes Excel.

Se añaden columnas/tablas de forma aditiva: archivos_tiff.activo, correcciones_tiff, atajos_numericos, expediente_preferido. Se conservan los atajos antiguos como datos históricos, pero el visor usa solo los numéricos. coding_schema_version pasa a 2.

## Identidad y registros anteriores

La regla operativa cambia a CURP + legajo; cambiar folio ya no justifica crear otra fila. El alta valida esa identidad y una protección SQLite impide nuevas altas duplicadas, incluso si los folios son distintos. Editar permite cambiar folio conservando el ID y la bitácora; CURP/legajo permanecen fijos.

La lista muestra una fila por CURP/legajo. Para registros creados con la regla anterior se conservan todas las filas y archivos; no se fusionan cantidades ni se eliminan antecedentes automáticamente. La columna registros indica cuántos registros coinciden dentro del filtro. Registros asociados permite abrir cada antecedente, ver sus TIFF y elegir el registro principal. Inicialmente se usa el primero activo; hasta revisar la elección, los datos y KPI de ese grupo son los de ese registro, no la suma de registros potencialmente duplicados. Los filtros se aplican antes de agrupar.

Si ya hay registros con distinta información, revisa Registros asociados y elige el operativo correcto. La actualización no inventa cuál de dos conteos o inventarios históricos es válido. No es una fusión automática de documentos. Un legajo 1 y un legajo 2 sí aparecen en filas separadas. Los archivos de los demás registros siguen accesibles desde Registros asociados.

No se tuvo acceso a la base SQLite de tu computadora; la causa específica de sus repeticiones no se pudo comprobar. Se corrigió la regla anterior que permitía repetir CURP/legajo en folios diferentes y se añadió esta vista agrupada con revisión de antecedentes.

## Alineación

Los valores y encabezados de todas las tablas basadas en Table se centran con el mismo anclaje. Las columnas conservan su desplazamiento horizontal cuando el texto es extenso.

## Visor

Casillas Archivos y Catálogo permiten mostrar/ocultar cada lateral. F11 o Solo imagen ocultan ambos; repetir restaura ambos. Se guarda la elección de visibilidad en la base. El divisor entre paneles continúa siendo arrastrable.

La rueda hace zoom alrededor del cursor. Shift+rueda desplaza verticalmente. Las barras y el arrastre permiten recorrer la imagen. Ajustar recalcula al cambiar el tamaño del panel; 100% permite evaluar el texto sin reducción. Se muestra el porcentaje de zoom.

Causa probable de la mala vista previa: Pillow usa vecino cercano para reducir modos 1 y P aunque se solicite otro filtro. La rotación fina de v0.2 convertía el binario a L y por eso cambiaba la calidad de visualización. Ahora la copia de pantalla se convierte a L/RGB antes de reducir con Lanczos. Esto no modifica los píxeles del TIFF guardado y no restaura detalles que el escáner no capturó. La prueba automática verifica tonos intermedios de antialias y bytes originales intactos.

Referencia técnica: https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.resize

## Atajos numéricos

- DP-n: Ctrl + n (DP-01 → 1; DP-15 → 15).
- FP-n: Ctrl + (100+n) (FP-01 → 101; FP-20 → 120). El 100 queda libre por defecto.
- HL-n: Ctrl+Shift + n (HL-01 → 1; HL-57 → 57).
- Configuración: cualquier número entre 1 y 999, con Ctrl o Ctrl+Shift. Incluye 100 y 120. No se inventan códigos de catálogo que no existan.

Para DP-15: mantener Ctrl, pulsar 1, soltar 1, pulsar 5, soltar 5, soltar Ctrl. Para HL-57: mantener Ctrl+Shift, pulsar 5 y 7 sucesivamente, soltar Ctrl para confirmar. Los números de varias cifras no son teclas únicas; la liberación de Ctrl determina el fin. Escape cancela. No se usa un temporizador, para no asignar el código 1 antes de acabar el 15 o el 100. Más de tres cifras cancela el atajo en vez de aplicar un número truncado.

Los atajos solo actúan en el visor/listas, no dentro de campos de texto. Se admite la fila numérica superior y el teclado numérico con Bloq Num. Atajos permite personalizar y exportar la lista vigente; se rechazan colisiones. Ctrl+S y Ctrl+Z siguen guardando/deshaciendo ajustes.

## Corrección práctica de escaneos

1. Selecciona el TIFF y la página defectuosa. Pulsa Marcar reescaneo.
2. Confirma la página digital y describe dónde localizar la hoja física: número, bloque de conteo, delante/detrás de qué documento, fecha, etc. Esa referencia no se infiere de la página digital porque no siempre coincide con una hoja física.
3. Escribe el problema. Aparecerá REESCANEAR en la lista y se creará una incidencia abierta.
4. En Reescaneos exporta la lista de localización para llevarla al escáner.
5. Reescanea e importa el nuevo TIFF en el mismo expediente/legajo. Verifica su imagen antes de vincularlo.
6. Reescaneos → Vincular nuevo TIFF y sustituir. Elige Solo página indicada o TIFF completo y confirma la revisión.
7. Organizar y generar reporte actualiza los destinos y métricas.

Solo página indicada: el nuevo TIFF debe contener exactamente una página. Se coloca en la posición marcada del TIFF anterior, se conserva la cantidad de páginas y se verifican los píxeles de las demás. La hoja suelta importada se retira del inventario para no contarla dos veces. Se conserva su original, el TIFF anterior a la edición y la relación en correcciones_tiff. Se resuelven las marcas de esa página, no las de otras páginas.

TIFF completo: exige igual número de páginas como guardia contra perder hojas; conserva el código del anterior. Revisa todas las páginas y su orden antes de confirmar. Se retira el archivo anterior y se vincula el nuevo. Si el reemplazo tiene intencionalmente otra cantidad de páginas, no uses este reemplazo automático: documenta la diferencia y realiza retirada/importación con resolución justificada de la incidencia.

Resolver con motivo sirve para anular una marca incorrecta o justificar que una hoja fue retirada porque no pertenece al expediente. No basta con escribir una acción para resolverla silenciosamente.

Restaurar imagen original después de sustituir una página reabre sus marcas de reescaneo, porque reaparecería el escaneo defectuoso original.

## Retirar, restaurar y recalcular

Retirar TIFF lo mueve a retirados y establece activo=0. Deja de aparecer en la lista operativa y no cuenta en los reportes. El original y la copia retirada se conservan; no existe eliminación física irreversible en esta versión. Retirados permite restaurarlo con motivo; vuelve a entrada para organizarlo de nuevo.

Renombrar un TIFF ya organizado lo lleva de vuelta a entrada. Organizar consulta el catálogo vigente y lo coloca en la carpeta correcta, por ejemplo al cambiar DP por HL. Retirar el último TIFF permite generar un inventario vacío de cero archivos/páginas, pero no permite cerrar el expediente con inventario vacío.

Las modificaciones invalidan el inventario previo y desmarcan la verificación de carpetas. Mientras haya correcciones pendientes no se emite un inventario completo. Al confirmar Organizar se miden los TIFF activos, se genera el reporte y se vincula automáticamente a ese trabajo/legajo; las pantallas de indicadores se refrescan. No se ejecuta el BAT heredado ni hace falta importar este reporte de nuevo.

Reportes TIFF distingue Actual, Histórico / sin asignar y Sin vigencia. No se eliminan las ejecuciones históricas; el inventario actual no suma ejecuciones. Si el mismo CURP/legajo tiene registros asociados, revisa primero cuál se usa como principal para los KPI.

## Pruebas y limitaciones

55 pruebas automatizadas únicas aprobadas en Linux con Python 3.12 y Pillow 12.3; sintaxis comprobada con gramática Python 3.8. Incluyen agrupación de identidades históricas sin borrar datos, bloqueo de altas duplicadas entre folios, cambio de folio con ID estable, previsualización binaria, secuencias 1/15/100/120, grupos Ctrl/Shift, reescaneo, reemplazo de una página MULTI, retiro/restauración e inventario cero.

No se verificó la interfaz en Windows 7 ni se ejecutó el wheel Windows/Pillow 9.5 en este entorno. La prueba local debe incluir teclado numérico, Ctrl+Shift, paneles en tu resolución y tres TIFF de ensayo (uno multipágina).

El diario de operaciones y los respaldos protegen cambios individuales, pero una sustitución completa o de página incluye varias operaciones; si se interrumpe, la corrección queda pendiente y se bloquea emitir el reporte hasta revisarla/reintentar. Respaldar datos completo, no solo SQLite.
