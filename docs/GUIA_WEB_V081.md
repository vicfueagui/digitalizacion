# Guía de oficina · candidata web 0.8.1-dev

Esta versión se revisa en una demostración separada. La aplicación diaria sigue siendo la web 0.8.0rc1 de INICIAR.bat y conserva los datos originales. No abras esta candidata con un workspace real ni uses las cuentas ficticias para operación.

## Abrir la candidata en esta HP

Ejecuta `C:\Digitalizacion\.development\ux-web-081-20261007\ABRIR_CANDIDATA_WEB081.bat`. Abre `http://127.0.0.1:8766`, distinto del puerto 8765 del acceso diario. Las credenciales ficticias están en LEEME_CANDIDATA.txt, junto al BAT. El workspace nuevo es demo-web; la carpeta candidato contiene solamente código y documentación. Mantén la consola abierta mientras pruebas y termina con Ctrl+C. Si esa misma demo ya está abierta, usa su dirección en el navegador en vez de arrancar otro servidor.

## Folios y expedientes: identificar antes de trabajar

En Recepción y folios, elige el folio y busca por nombre o CURP. Puedes filtrar esperados, cotejados, faltantes, discrepancias y devueltos. Los seis totales de cabecera describen el folio completo; el texto de elementos visibles indica el resultado del filtro. Un devuelto también puede haber sido cotejado: no sumes estas categorías como si fueran excluyentes.

Cada fila conserva CURP + legajo, ciclo, recepción e integración. Despliega Detalle y diferencias para ver sus hojas, TIFF y páginas. La etiqueta histórica identifica una recepción anterior o un ciclo que ya no es el principal. Expediente 360 abre el ciclo de esa fila y muestra la recepción consultada; el encabezado operativo sigue identificando la integración actual. Ver expedientes vigentes asociados aplica el filtro sin convertir un ciclo viejo en principal.

Las casillas permiten cotejar varios elementos. Seleccionar visibles afecta las filas del resultado actual; Shift permite seleccionar un tramo. Antes de confirmar, comprueba físicamente identidad y legajo. La lista esperada no acredita recepción. Los datos del acuse, quién entrega y quién recibe se consultan en Datos de recepción física.

## Conteo físico ágil

Desde Expediente 360 abre Conteo físico. La pantalla identifica la integración que estás contando. Escribe las hojas de un bloque y pulsa Enter; se registra el bloque y vuelve el foco a Cantidad. Repite para todos los bloques. Puedes modificar o anular un bloque abierto con motivo; los anteriores permanecen en el historial.

Al terminar, coteja el total mostrado y marca «He comprobado que esta integración contiene X hojas físicas». Solo entonces confirma. Un conteo confirmado exige Reabrir con motivo y confirmación explícita antes de corregirlo. Una pestaña desactualizada no puede confirmar los bloques que otra operación cambió: vuelve a revisar el total.

Las hojas históricas aparecen aparte. No las captures otra vez cuando llegue una integración. Hoja física, archivo TIFF y página digital son tres unidades distintas; su diferencia no prueba por sí misma un error. Una nueva entrega vuelve a calcular los totales del expediente completo mediante los servicios existentes.

## Estación de codificación

Abre Codificación desde Expediente 360. A 1366 × 768 se muestran tres paneles simultáneos: archivos, visor y catálogo. Arrastra los separadores para ajustar anchuras; también aceptan las flechas del teclado al tener el foco. Archivos y Catálogo permiten ocultar paneles; Restablecer paneles recupera su distribución. Menú vuelve a mostrar la navegación general. Puedes activar pantalla completa.

El explorador ofrece lista o miniaturas, búsqueda por nombre/código y orden por importación, nombre, código o fecha del archivo fuente. La flecha invierte el orden. Las miniaturas se solicitan al necesitarlas; no se decodifica el lote completo al abrir la estación. El documento activo tiene borde guinda, título y página actual.

Un clic abre el TIFF. Las casillas, Ctrl+clic y Shift+clic seleccionan varios; Ctrl+A selecciona los visibles. Limpiar selección evita aplicar después un código a un grupo que ya no necesitas. El contador distingue selección visible de elementos ocultos por un filtro. Las acciones se aplican a la selección visible; sin selección, el botón del código se aplica al documento activo.

Busca en el catálogo por código, título o descripción. Pulsar el código y usar su atajo registrado llegan a la misma operación de negocio. Las estrellas guardan favoritos de TU cuenta, independientes de otros usuarios y de los atajos globales. Todos/Favoritos cambia el ámbito del catálogo sin modificarlo. Las anchuras, vista, paneles ocultos y Avanzar después de codificar también se guardan por cuenta.

Para un lote se muestra la cantidad y los nombres antes de confirmar. Al terminar se informan IDs completados y pendientes. Un corte puede dejar una parte terminada: revisa el resultado y Recuperar operación; nunca supongas que todo se deshizo. La aplicación no reintenta escrituras automáticamente. Retirar conserva evidencia e historial; activa Mostrar retirados para seleccionarlos y recuperarlos. Una selección mezclada de activos y retirados se rechaza para que puedas corregirla.

## Teclas dentro de la estación

| Tecla | Acción |
| --- | --- |
| F7 / F8 | TIFF anterior / siguiente del filtro y orden actuales |
| RePág / AvPág | Página anterior / siguiente del TIFF multipágina |
| + / − / F | Acercar / alejar / ajustar al visor |
| F2 | Renombrar con validación del nombre y conservación de versiones |
| Ctrl+O | Abrir importación |
| Ctrl+A | Seleccionar archivos visibles |
| Supr | Preparar retiro de la selección; exige confirmación |
| Ctrl o Ctrl+Shift + dígitos | Atajo real del catálogo; mantener Ctrl y soltar al terminar la secuencia |
| F6 | Alternativa: escribir el código y pulsar Enter |
| Escape | Cancelar secuencia o recorte / cerrar diálogo |

Los atajos de trabajo se suspenden al escribir en búsquedas, cantidades, motivos y otros campos. Algunos atajos de Ctrl pertenecen también al navegador; si este los intercepta, usa F6 o el botón del catálogo. No se instalan ganchos globales de teclado ni se reasignan atajos reservados.

## Revisar y corregir imágenes

El visor permite cambiar páginas, ajustar, ampliar y desplazar la imagen ampliada arrastrándola. Ver original alterna consulta del original importado; Historial permite consultar revisiones y restaurar el original con una nueva revisión. No se editan las vistas de evidencia: vuelve a Actual antes de girar o recortar.

Giro fino admite décimas de grado. Recortar marca un rectángulo sobre la página y exige confirmación y motivo. La operación conserva las demás páginas del TIFF y el historial. Si la fuente está mal escaneada, Reescaneo registra la página y su referencia física. Usa el flujo existente de sustitución y validación antes de entregar.

Organizar / entregar sigue creando una versión NUEVA del expediente completo actualizado. Las entregas anteriores son inmutables. Generar la entrega no acredita aprobación: revisa la versión exacta, resuelve observaciones y aprueba explícitamente. La custodia física se registra por separado.

## Leer los indicadores sin confundir unidades

Aplica periodo, dimensión, fuente, fecha inicial/final, folio, digitalizador y estado. Los filtros activos quedan visibles. Los gráficos locales tienen listas o tablas con las mismas cifras para consulta accesible.

- Inventario: ciclos vigentes y CURP distintas; varios legajos pueden compartir CURP. Sus fechas filtran la recepción inicial del ciclo.
- Etapas: Por aprobar y Cerrados se presentan separados. Sin expedientes, el porcentaje muestra Sin base.
- Codificación: TIFF activos codificados o pendientes; códigos frecuentes hasta doce categorías.
- Calidad: observaciones, reescaneos pendientes, versiones de entrega y conteos sin confirmar. Una versión de entrega no equivale a otro expediente.
- Recepción por folio: elementos esperados/cotejados y diferencias. Un filtro de responsable/estado excluye elementos sin ciclo atribuible. Un filtro de fechas excluye recepciones sin fecha registrada.
- Actividad: recepciones iniciales e integraciones por su fecha registrada. Sin fecha se informa aparte; no se inventa una fecha actual por migración.
- Cubo: Inventario por recepción mide los documentos activos asociados a cada integración. Ingresos TIFF mide importaciones registradas, incluso documentos retirados después; no acredita cuándo se escaneó físicamente. Hojas y conteos muestran No aplica para esta última fuente.

CSV del cubo filtrado descarga las filas y unidades de la tabla del cubo bajo los mismos filtros. No exporta todos los expedientes ni las imágenes. La etapa del análisis es la actual, no una reconstrucción de estados históricos.

## Seguridad, preferencias y reversión

La candidata conserva autenticación, roles, CSRF, DEBUG=False, atención serial y diario durable. Solo escucha en este equipo. Los TIFF se sirven con sesión válida, sin exponer rutas físicas. No requiere instalaciones nuevas, conexiones a CDN ni servicios programados.

La única migración añadida es webapp.0001_deskpreferences en la base privada de cuentas `.web/acceso.sqlite3`: crea una tabla por usuario para favoritos y diseño. No altera la base de expedientes (núcleo 8 / TIFF 3). El respaldo web existente incluye las preferencias junto con las cuentas; sigue siendo privado. La migración es reversible eliminando esa tabla, pero eso pierde las preferencias: no ejecutes esa reversión sobre la aplicación de trabajo sin respaldo y plan de mantenimiento.

Para dejar de evaluar, cierra la consola de esta candidata con Ctrl+C y vuelve al acceso diario INICIAR.bat. No hay que restaurar datos ni volver al escritorio. No copies código candidato encima de la raíz: una promoción futura necesita autorización de esta etapa, respaldo privado actual, validación de una copia, resguardo del código y actualización verificada del manifiesto de activación. Conservar el runtime y `.development`.

## Alcance pendiente

El ensayo automático y las capturas usan datos ficticios. Falta aceptación de una jornada humana, especialmente ergonomía de cientos de documentos, atajos que puede interceptar Edge y tamaño real de los TIFF del escáner. El lugar previsto para sugerencias documentales está oculto; no existe OCR ni clasificación automática en esta entrega.
