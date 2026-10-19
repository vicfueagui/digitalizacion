# Expedientes y estación TIFF · candidata 0.8.2

Esta guía corresponde a una candidata separada con documentos ficticios. La aplicación diaria de `C:\Digitalizacion\INICIAR.bat` sigue en 0.8.0rc1. No copies la candidata sobre esa instalación ni la abras sobre sus datos.

## Abrir y orientarse

Abre `C:\Digitalizacion\.development\tiff-web-082-20261008\ABRIR_CANDIDATA_WEB082.bat`. La dirección es `http://127.0.0.1:8767`. El archivo LEEME_CANDIDATA.txt junto al acceso indica la cuenta exclusivamente ficticia. Mantén la consola abierta; termina con Ctrl+C.

En Expedientes, filtra por nombre/CURP, folio, responsable y estado. El resumen y la tabla corresponden al mismo ámbito de ciclos principales. Una CURP con varios legajos ocupa varias filas. Las hojas físicas, los TIFF activos y las páginas digitales tienen columnas distintas. Los conteos pendientes no se convierten en cero confirmado. Una incidencia sin resolver sigue siendo una incidencia aunque sus TIFF hayan cambiado.

Abre el expediente y pulsa **Estación de codificación**, o utiliza **Codificar** desde la tabla o la mesa TIFF. El catálogo permanece a la derecha, la imagen al centro y los archivos a la izquierda. La navegación general se oculta dentro de la estación; Menú permite recuperarla. Volver al expediente conserva el acceso a los filtros de origen cuando se llegó desde la tabla.

Arrastra los separadores o enfócalos con Tab y usa las flechas. Restablecer distribución recupera los tres paneles. Puedes ocultar voluntariamente cada lateral y usar pantalla completa. La distribución y la vista se guardan en tu cuenta. En una ventana demasiado estrecha se avisa que hay desplazamiento horizontal; el catálogo no desaparece silenciosamente.

## Archivos e importación

Las cuatro vistas comparten documento activo, selección, búsqueda y orden:

- **Iconos:** símbolo TIFF y estado; no descarga las imágenes del lote.
- **Lista:** nombres compactos; pasa el puntero o enfoca el botón para consultar el nombre completo.
- **Detalles:** columnas de nombre, código/estado, páginas, tamaño, fecha fuente e importación/creación. Las cabeceras permiten ordenar; el panel tiene desplazamiento horizontal propio.
- **Miniaturas:** primera página, nombre y páginas, con tamaño ajustable. Se solicitan de forma diferida; la caché del servidor se limita a 64 miniaturas.

Importar TIFF admite varios archivos. Importar carpeta utiliza el selector de carpetas del navegador y toma **solo los TIFF directamente dentro de ella**. Las subcarpetas y otras extensiones se indican como omitidas. La selección inicial muestra nombres, cantidad, tamaño y destino. Después, el servidor comprueba el contenido de todas las páginas, límites y duplicados; una extensión .tif no basta.

Confirma únicamente después de revisar el lote. Cancelar no añade documentos al expediente. El límite existente es 100 archivos y 200 MB por lote, con páginas de hasta 36 millones de píxeles en modos admitidos. Los duplicados idénticos del mismo ciclo se omiten. Las importaciones pueden terminar parcialmente: el resultado indica completados y pendientes; no repitas ciegamente una solicitud interrumpida.

El navegador envía bytes, no rutas del servidor. La fecha de modificación comunicada por el navegador se identifica como **fecha del archivo fuente**, no como prueba de cuándo se escaneó. La fecha de creación original de Windows no está disponible. Un derivado se identifica como tal y no recibe una fecha fuente inventada.

## Selección y codificación

El documento activo es el que ves en el centro. Las casillas, Ctrl+clic y Shift+clic forman una selección independiente. Visibles selecciona el resultado filtrado; Limpiar selección deja de seleccionar. Si un filtro oculta parte de la selección, el contador lo indica y una operación pide elegir expresamente trabajar solo con los visibles; Cancelar permite revisar el alcance.

**El clic en un código aplica al TIFF activo.** Para codificar varios, marca Aplicar a selección, elige el código y revisa los destinatarios antes de confirmar. El servicio reserva nombres sin sobrescribir. Los completados se retiran de la selección para evitar repetir el lote. Avanzar al pendiente usa el orden anterior al renombrado, y busca el siguiente TIFF activo sin código.

Busca por código, título o descripción y filtra DP/FP/HL. Las estrellas y Todos/Favoritos pertenecen a tu cuenta; no cambian el catálogo global. Los favoritos mantienen el orden en que se añadieron. El respaldo web incluye estas preferencias junto con las cuentas.

Los números que aparecen en cada fila se pueden usar con **Secuencia numérica**: pulsa ese botón (o F6 cuando el navegador lo entregue a la página), selecciona DP/FP o HL, escribe todos los dígitos y pulsa Enter. Por ejemplo, DP-15 usa 15 en DP/FP; FP-20 usa 120; HL-100 usa 100 en HL. No hace falta escribir DP-15 ni otro código completo. Un número desconocido o de más de tres dígitos no asigna un prefijo.

Los atajos heredados Ctrl/Ctrl+Shift y dígitos se conservan si el navegador los entrega; la acción espera a soltar Ctrl. Edge puede reservar combinaciones para pestañas y controles. El botón de secuencia evita depender de esas combinaciones. No hay captura global del teclado. Los campos de búsqueda, motivos y otros formularios mantienen sus teclas normales.

F7/F8 cambia de TIFF; RePág/AvPág de página; +/− amplía/reduce; F ajusta; Ctrl+S guarda ajustes; Ctrl+Z deshace un ajuste; F2 renombra; Ctrl+O importa; Ctrl+A selecciona visibles; Supr prepara retiro con motivo.

## Revisar y editar

La cabecera muestra la identidad, folio, legajo, ciclo e integración. La imagen indica **Actual, Ajustes sin guardar, Original o Revisión**. Original y revisiones son evidencias de consulta; vuelve a Actual para editar.

Usa Ajustar, Ancho o 100%, rueda para zoom, Shift+rueda para desplazar y arrastre para recorrer la imagen. Los giros de 90° y 180° se añaden a los ajustes pendientes. Grados admite valores con signo entre −180 y 180. El giro fino interpola píxeles y puede convertir una página binaria a gris; revisa el resultado.

Recortar permite arrastrar un rectángulo. La vista previa reducida muestra el resultado propuesto; confirmar lo añade a los ajustes pendientes. Cancelar conserva la imagen anterior. Deshacer elimina el último ajuste pendiente; Descartar elimina todos; Sin ajustes permite comparar con la versión guardada. **Guardar ajustes** procesa el TIFF fuente completo con la operación aplicada solo a la página elegida y conserva una revisión.

Cambiar de documento, página, código o enlace interno con ajustes pendientes ofrece Guardar / Descartar / Cancelar. Al cerrar o recargar la pestaña, el navegador solo permite su aviso genérico de cambios pendientes: cancela el cierre y usa Guardar o Descartar dentro de la estación. No puede ofrecerse un diálogo personalizado después de cerrar la pestaña.

Los originales conservan sus bytes. El servicio verifica las páginas no editadas, DPI y píxeles; guarda con compresión Deflate sin pérdida. La rotación fina y el recorte sí alteran la página elegida. Se conservan las etiquetas descriptivas y perfil ICC admitidos, **no se promete conservar todas las etiquetas privadas del escáner**. Las vistas reducidas nunca son la fuente de la escritura.

Revisiones permite consultar una versión y restaurarla creando otra revisión. Reescaneo mantiene separados número de página digital y referencia física: no deduzcas uno del otro. Retirar y Recuperar requieren motivo y conservan evidencia; no borran el original.

## Dividir, extraer y unir

Estas funciones actúan sobre versiones actuales de TIFF activos de **la misma integración actual, ciclo y legajo**. Las integraciones anteriores se consultan; no se mezclan con otra recepción para derivar páginas. Los diálogos muestran fuentes, orden, salidas previstas y efecto sobre las páginas activas.

**Dividir** ofrece una página por archivo, antes/después de la página actual, puntos de corte, grupos de N y rangos completos. Los puntos indican cortes después de esas páginas. En rangos completos usa, por ejemplo, `1-3;4-6;7-10`. Cada página debe aparecer exactamente una vez; un hueco o solapamiento se rechaza. La opción recomendada sustituye la fuente mediante retiro trazable después de verificar todos los resultados.

**Extraer** permite página actual, lista no consecutiva o rangos, como `1,3,5-7`. Elige un TIFF multipágina o uno por página. Copiar conserva la fuente activa y **aumenta** las páginas del inventario. Mover conserva el total: se retira la fuente y se crean resultados más un remanente con identidad nueva, si quedan páginas. La procedencia conserva la relación con la fuente; no se fabrica un TIFF vacío.

**Unir** requiere al menos dos seleccionados. Las flechas del diálogo cambian el orden de los archivos. Cada fuente también permite escribir su orden de páginas, por ejemplo `3,1-2`; debe incluir todas sus páginas una sola vez. La vista previa enumera el orden exacto. Confirma el TIFF multipágina previsto y decide conservar las fuentes activas o sustituirlas mediante retiro trazable. Para tomar solo algunas páginas, prepara antes una extracción.

Los derivados quedan **pendientes de codificación** por defecto. Conservar código exige selección explícita y que todas las fuentes compartan un mismo código activo. Una unión de códigos distintos nunca hereda silenciosamente el primero. Las identidades nuevas registran por página el ID y versión fuente, número de página y operación; consulta esa procedencia desde Revisiones. El límite por operación es de 500 fuentes y 2000 páginas.

Se prepara y verifica cada salida antes de activar las altas y los retiros en una única transacción de metadatos. La base y el disco no forman una transacción única. Si se interrumpe antes de confirmar, las fuentes siguen activas y el trabajo bloquea nuevas escrituras hasta **Recuperar operación**. La preparación fallida se conserva fuera del inventario; no se elimina automáticamente. Si el commit terminó, la recuperación no lo deshace ni duplica los resultados. Tras una respuesta incierta, revisa el historial antes de formular otra operación.

Estas operaciones invalidan el inventario/validación vigente. Las entregas históricas permanecen intactas, las incidencias y reescaneos siguen pendientes y **el conteo físico no cambia**. Organizar / entregar genera después otra entrega completa actualizada; todavía requiere revisión y aprobación. Los derivados se excluyen de Ingresos TIFF para no presentarlos como nuevos escaneos/importaciones.

## Jornada ficticia para aceptar la candidata

1. Abre Expedientes, filtra DEMO y comprueba nombres, legajos, hojas, TIFF, páginas y pendientes.
2. Abre la estación desde Codificar. Revisa cuatro vistas, selección, paneles y retorno. Prueba también tu zoom de Windows/navegador.
3. Importa un lote y una carpeta ficticios. Cancela una vista previa y comprueba que no cambió el inventario. Repite un TIFF y observa el duplicado omitido.
4. En un multipágina, gira y recorta; prueba Cancelar, Descartar y Guardar al navegar. Consulta Original y revisiones.
5. Divide un multipágina, extrae una copia y prepara una unión reordenada. Compara los totales y las páginas antes de confirmar.
6. Codifica mediante clic, selección y secuencia numérica. Guarda favoritos; sal y entra para comprobar persistencia.
7. Revisa los totales del expediente, las incidencias pendientes y las entregas anteriores. La comodidad de una jornada humana sigue siendo una valoración del operador.

## Instalación futura

La candidata añade solo `procedencia_paginas` al esquema TIFF (3 → 4, núcleo 8 intacto). Conserva la migración de preferencias de la candidata anterior en la base de cuentas. Las pruebas de migración y respaldo usan bases ficticias; no se ha migrado la base diaria en esta fase.

Instalar requiere autorización de esta etapa, pausa actual de escrituras, respaldo privado de datos/cuentas y código, validación sobre copia y activación del paquete verificado. La herramienta de primera transición no actualiza una web ya activada ni sustituye el ensayo de esta migración. No usar las autorizaciones históricas de instalación o GitHub. Una base con esquema TIFF 4 no debe abrirse con código anterior que solo admite 3. No reviertas borrando procedencias ni restaures una base antigua sobre nuevas capturas. Para dejar de evaluar basta cerrar la consola de la candidata y abrir el acceso diario.
