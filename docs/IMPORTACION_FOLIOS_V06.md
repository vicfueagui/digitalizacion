# Listas de préstamo, legajos y directorio · 0.6.0

Esta ampliación permite registrar una lista nominal por folio y completar después el desglose físico. Complementa el [manual operativo](OPERACION_V05.md). Los ejemplos de la demo son inventados.

**Actualización 0.6.1:** ya puedes aceptar una selección sin recapturar CURP, confirmar el legajo común de los registros que lo omiten y crear sus ciclos en un solo paso. Consulta [Recepción práctica e indicadores](RECEPCION_INDICADORES_V061.md). Las acciones adicionales del préstamo están en el menú Más acciones.

## Importar Excel o CSV

1. En **Expedientes → Importar lista de folio Excel / CSV**, selecciona un `.xlsx`, `.csv` o `.tsv`. También está disponible en Folios y en Importación y respaldo. No uses «Excel inicial» para las listas de préstamo diarias.
2. Selecciona la hoja y revisa la fila de encabezados. Se reconocen encabezados reordenados, acentos, signos y variantes habituales. Si un nombre es ambiguo, selecciona su correspondencia manualmente. No se adivinan las identidades.
3. Si el archivo omite folio o área, puedes indicar el valor común. **Deja Legajo vacío cuando no aparezca en la lista.** Solo aplica un legajo común si lo has comprobado para todos los registros afectados.
4. Pulsa **Actualizar vista previa** después de cambiar columnas u opciones. Revisa los resultados y confirma la importación. El original permanece intacto.
5. La aplicación abre Folios y selecciona el folio si la lista contiene uno solo. En **Recepción / préstamo** encontrarás las CURP, nombres, metadatos y legajos pendientes.

| Columna de la lista | Uso |
|---|---|
| CURP O RFC | Identidad CURP; un RFC sin CURP válida queda por aclarar |
| CURP O RFC2 | Comprobación opcional; si difiere, la fila queda pendiente |
| No. | Consecutivo original; nunca número de legajo |
| APELLIDO PATERNO, MATERNO, NOMBRE | Nombre completo, sin dividirlo ni cambiar su orden |
| folio | Agrupa uno o muchos expedientes; un archivo puede incluir varios folios |
| Integra | Persona declarada en la lista, reutilizable en el directorio; no asignación automática |
| sistema | Sistema declarado, reutilizable en el directorio |
| fecha solicitud | Fecha de la solicitud; no acredita recepción física |
| TRABAJADOS | Declaración de origen; no marca avance, aprobación ni cierre |

CSV admite separadores coma, punto y coma, tabulación o barra vertical; codificaciones UTF-8, UTF-8 con BOM, Windows-1252 y UTF-16 con BOM. Excel admite `.xlsx`, sin instalar Excel ni una biblioteca adicional. Guarda `.xls` antiguos como `.xlsx` o CSV. Los libros con calendario de fechas 1904 deben convertirse antes a CSV o al calendario 1900. En CSV usa fechas día/mes/año o año-mes-día.

Las filas incorrectas se conservan en **Importación y respaldo → Pendientes**, con fila y valores originales. Las válidas se registran en la misma operación. Para subsanar un archivo, guarda una copia corregida y vuelve a analizarla: las identidades existentes se reutilizan sin sobrescribir recepción, custodia, asignación ni los datos anteriores. Un cambio de nombre/área sobre una identidad existente requiere conciliación; no reemplaza silenciosamente el dato.

Repetir exactamente el archivo, hoja y configuración devuelve el resultado anterior. Si cambias el contenido, se analiza como otra importación; los elementos ya registrados no se duplican. Cuando ya existen legajos y una nueva lista no los declara, la fila queda pendiente de conciliación. Si existía un elemento sin legajo y otra lista lo especifica, confirma el desglose en Recepción / préstamo y revisa el pendiente: repetir el mismo archivo no lo reprocesa.

## Una CURP con varios legajos físicos

Una lista sin legajo registra la persona y su asociación al folio. Permanece visible en **Folios → Recepción / préstamo**; todavía no crea un ciclo sin identidad física.

Selecciona el elemento y pulsa **Registrar / añadir legajos de esta CURP**. Indica, por ejemplo, `1,2,3`, y la evidencia del cotejo físico. El primer legajo aprovecha el elemento pendiente; los demás reciben su propio elemento y ciclo. No se toma el consecutivo No. como legajo. Si un legajo ya existe en ese folio, se reutiliza sin duplicarlo.

Los ciclos aparecen en Expedientes. Selecciona cualquiera y usa **Ver / añadir legajos de la misma CURP** para navegar o registrar otro. También se accede desde Expediente 360. Cada legajo conserva por separado sus conteos, TIFF, páginas, entregas y revisión. Todos mantienen su vínculo con la CURP y, cuando provienen de una lista, con el archivo y fila de origen, incluso los añadidos posteriormente.

El alta técnica usa la etapa inicial del sistema; la columna **Recepción** continúa Pendiente. Registra entrega/recepción del folio, coteja y acepta cada legajo físico antes de asignarlo. Crear legajos no acredita que se hayan recibido o trabajado. Un nuevo folio de la misma CURP y legajo genera otro ciclo y conserva los anteriores.

## Catálogos reutilizables

En **Catálogos → Áreas / personas / sistemas / ubicaciones** puedes crear, buscar, editar, desactivar y reactivar entradas. Los campos operativos muestran selectores con botón **+ / Editar**, de modo que puedes alimentar el catálogo sin abandonar la captura. Los nombres nuevos se incorporan al guardar la operación correspondiente.

Personas se reutiliza para quien entrega, recibe, integra, es responsable, revisa, digitaliza o recibe una devolución. Áreas, sistemas y ubicaciones físicas tienen categorías separadas. Las identidades CURP de los expedientes permanecen en su registro de personas del expediente.

Los nombres se comparan sin distinguir mayúsculas, espacios repetidos o acentos. Editar conserva el ID y reconoce el nombre anterior como alias; los nombres capturados en eventos históricos permanecen como evidencia. La baja es lógica: impide nuevas selecciones y permite reactivar después, conservando vínculos e historial. No borra préstamos ni asignaciones.

## Tabla y búsqueda

Expedientes prioriza CURP, nombre, folio, legajo, estado, **TIFF**, **Páginas**, hojas físicas, digitalizador y recepción. Los totales corresponden a archivos activos del ciclo mostrado, sin sumar copias de entregas ni ciclos históricos. Cero significa que todavía no hay archivos activos registrados; no confirma que el expediente esté digitalizado. Fuera del broche y carpetas conservan sus datos y funciones; se retiraron únicamente de esta tabla principal.

CURP/nombre, folio y digitalizador buscan coincidencias parciales mientras escribes, con una pausa de 220 ms. La búsqueda de texto ignora acentos y mayúsculas. Los filtros combinan sus condiciones; una fecha incompleta muestra una indicación y se aplica al completarla. El folio también puede coincidir con ciclos históricos de la identidad mostrada. «Registros asociados» permite consultarlos.

Es el equivalente local de una búsqueda AJAX: no requiere navegador, servidor ni red. La búsqueda consulta los metadatos y conserva la selección cuando sigue visible; no abre los TIFF ni reconstruye el Kanban por cada tecla.

## Ensayo breve

Cada demo nueva incluye `ejemplos/lista_folio_sintetica.csv`, con tres personas ficticias del mismo folio y sin legajo. Impórtala, desglosa la primera CURP en `1,2,3`, comprueba que puedes navegar entre ellos, acepta físicamente uno y asígnalo seleccionando una persona del directorio. Importa un TIFF solo en el legajo 2: los otros deben conservar sus propios conteos. Repite la importación y confirma que no se duplica.

Para los datos de oficina, aplica primero el [procedimiento de actualización protegido](WINDOWS7.md). La versión 0.6.0 migra a núcleo 7 / TIFF 3 con snapshot y transacción; incorpora directorio y procedencia de listas, enlaza nombres existentes y conserva IDs, textos históricos y documentos.
