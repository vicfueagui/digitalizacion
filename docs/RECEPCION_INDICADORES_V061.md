# Recepción práctica e indicadores · 0.6.1

Esta versión simplifica el paso de una lista importada a Expedientes y rediseña Indicadores. Mantiene núcleo 7 / TIFF 3: una instalación 0.6.0 no necesita migrar su esquema. No altera por sí sola las recepciones previas.

## Aceptar sin volver a escribir CURP

1. Importa la lista Excel/CSV como antes. Si contiene un solo folio, puedes usar **Continuar con recepción** al terminar. También puedes abrir **Folios → Recepción / préstamo**.
2. Selecciona los expedientes físicos que cotejaste. Usa **Seleccionar visibles** para toda la lista mostrada, Shift para un rango o Ctrl/Cmd para varios. El buscador CURP/nombre y el filtro de recepción permiten reducir la selección.
3. Pulsa **Aceptar seleccionados**. La vista previa muestra la CURP importada, nombre, legajo y comprobación de cada elemento. No se solicita recapturar CURP.
4. Si algunos registros no traen legajo, el diálogo propone **1** y lo muestra explícitamente en la vista previa. Puedes cambiar ese número común. Se aplica únicamente a los elementos que no tienen legajo; conserva los números ya registrados. Si hay varios físicos de una CURP, usa **Más acciones → Registrar / añadir legajos** para definirlos antes o añadirlos posteriormente.
5. Marca **He cotejado estos expedientes físicos…** después de revisar los datos. Puedes añadir una nota o acuse; la evidencia básica, el operador y la fecha se registran automáticamente.
6. Pulsa **Aceptar y crear expedientes**. Los elementos se aceptan individualmente dentro de una sola operación y sus ciclos aparecen en Expedientes. Usa **Ver en Expedientes** para abrir esa vista filtrada por el folio.

La aceptación individual registra su fecha de recepción si todavía faltaba. No inventa el área, quién entregó ni el acuse de todo el folio: esos datos siguen en **Más acciones → Registrar entrega / recepción del folio**. Asignación y devolución física se conservan como acciones separadas.

**Revisar diferencia** abre el formulario individual con CURP y legajo precargados para registrar una discrepancia, un faltante o aclarar un recibido fuera de lista. La aceptación rápida se detiene si la selección contiene discrepancias, faltantes, identidades repetidas, elementos de otro folio o préstamos en devolución. Puedes filtrar por Pendiente y aceptar los elementos que sí cotejaste. No cambia ni descarta las excepciones silenciosamente.

Cancelar la vista previa no cambia datos. Repetir una aceptación conserva la evidencia original y no duplica expedientes. Si falla la escritura de algún elemento, toda la selección se revierte. «Seleccionar visibles» solo afecta las filas que aparecen con los filtros actuales.

## Indicadores

Los filtros están dentro de la pestaña y se comparten con Expedientes: CURP/nombre, folio, digitalizador, estado y fechas de recepción. La búsqueda se actualiza al escribir. El rótulo superior identifica si es una vista filtrada, cuántos expedientes activos incluye y a qué hora se actualizó. Una fecha incompleta se indica para que no parezca un filtro ya aplicado.

- **Resumen:** tarjetas de expedientes vigentes, CURP distintas, TIFF activos y páginas registradas. Una CURP con tres legajos cuenta como tres expedientes y una CURP.
- **Etapas del proceso:** por iniciar, digitalización, revisión, corrección, por aprobar y cerrados, con cantidad y porcentaje visibles junto a cada barra. Se separan los listos para aprobación de los cerrados.
- **Cobertura:** recepción aceptada, digitalizador asignado, conteo físico confirmado, al menos un TIFF registrado y cierre registrado. Cada porcentaje usa como base los expedientes activos de la vista; estas coberturas se superponen y no deben sumarse.
- **Por folio / digitalizador:** tabla con expedientes, aceptados, TIFF, páginas, cerrados y porcentaje de cierre. Abre un grupo para consultar sus expedientes.
- **Todos los indicadores:** cifras anteriores más hojas físicas, pendientes de recepción/asignación/conteo, incidencias, observaciones e inventarios registrados como desactualizados.

Selecciona una barra para consultar los expedientes que la componen y abrir su vista 360. También puedes enfocar el gráfico con Tab, recorrer barras con flechas y abrirlas con Enter. El resumen permite desplazamiento vertical cuando la ventana tiene poca altura.

Las barras usan colores de texto explícitos y reservan espacio para cifras y porcentajes; se redibujan al cambiar el ancho. Con cero resultados, los conteos muestran cero y los porcentajes **Sin base**, no un avance ficticio. Las fechas filtran la recepción de los ciclos, no la fecha de solicitud de una lista ni una serie histórica de productividad.

El aviso **Fuera de Expedientes** cuenta globalmente los elementos de folios activos que aún no tienen ciclo. Está separado de las métricas filtradas y permite ir a Folios para continuar su recepción. No se incluye en el denominador del proceso hasta crear sus ciclos.

## Qué miden las cifras y qué se exporta

Se muestran metadatos registrados de los archivos activos del ciclo vigente. No se suman copias de entregas, archivos retirados, otros ciclos históricos ni declaraciones TIFF de reportes legados. Los estados de proceso/cierre son los registrados; para comprobar contenido, integridad y vigencia antes de aprobar, usa Expediente 360. El panel evita abrir y calcular hashes de los TIFF durante la búsqueda o el redimensionado.

**Exportar indicadores** genera una carpeta nueva con indicadores, etapas, coberturas, agrupaciones, expedientes de esa misma vista y `contexto.json` con sus filtros, fecha y alcance. No incluye automáticamente todo el historial ajeno a los filtros. Exportaciones 360/datasets e historiales existentes permanecen disponibles en sus funciones correspondientes.

## Prueba en esta Mac

Abre **Digitalizacion-Pruebas-OSX-061.command** en el Escritorio. Usa el código independiente 0.6.1 y permite continuar las sesiones 0.6 existentes o crear otra demo ficticia. Conserva los accesos y código anteriores; cierra una demo antes de abrirla desde otra versión.

Cada demo trae `ejemplos/lista_folio_sintetica.csv`. Importa el CSV sin asignar legajo, continúa con recepción, selecciona sus tres registros y acepta con el legajo común mostrado. Deben aparecer tres expedientes. Añade después otro legajo a una CURP y comprueba que sus métricas permanezcan separadas. En Indicadores busca un folio inexistente: deberá mostrar cero y Sin base; limpia el filtro para recuperar el resumen.

La revisión gráfica en Mac no certifica Windows 7. Sigue [WINDOWS7.md](WINDOWS7.md) para el ensayo local de oficina antes de actualizar datos productivos.
