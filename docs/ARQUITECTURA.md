> Antecedente histórico. Para la entrega actual, consultar [VALIDACION_V05.md](VALIDACION_V05.md) y [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md).

> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

> Documento de la base v0.1. Para el módulo nuevo y sus cambios consulta CODIFICACION.md y VALIDACION_V02.md.

# Arquitectura y reglas operativas

## Decisión de tecnología

Aplicación de escritorio Python + Tkinter + SQLite. Las tres piezas vienen en el instalador completo de Python para Windows. La separación entre core, importers y ui permite conservar las reglas al cambiar la interfaz. VS Code es el editor: no es la aplicación ni la base de datos.

Esta primera versión convierte el Excel en una fuente de entrada, no en un servidor de datos editable por formularios. Es una decisión deliberada: una base relacional facilita claves únicas, relaciones, transacciones e historial. No se exige instalar un servidor de base de datos. La memoria total real se deberá medir en el Lanix; no se procesan imágenes TIFF ni OCR en esta aplicación.

Uso local de un operador, base en disco local, no en carpeta compartida de red. El nombre de operador de la bitácora es declarativo: no hay autenticación, roles ni firma electrónica. La base no está cifrada. No es un sistema institucional multiusuario definitivo.

## Entidades y granularidad

| Entidad | Una fila representa | Clave / relación |
|---|---|---|
| personas | Persona | CURP única, normalizada |
| folios | Asignación de trabajo | Número con año, por ejemplo 833/2026 |
| trabajos | Legajo encargado en un folio | ID interno; única combinación folio/CURP/legajo |
| conteos | Bloque de hojas contado | Trabajo; cantidad positiva; baja lógica |
| catalogos | Código de documento o tipo de incidencia | Tipo + código únicos; activo/inactivo |
| incidencias | Problema observado y acciones | Trabajo; referencia al catálogo y copia del código |
| ejecuciones | Reporte completo de una ejecución del BAT | Huella del contenido; vínculo confirmado al trabajo |
| historial | Permanencia en una etapa | Trabajo; inicio, fin, motivo, operador |
| tareas | Tarjeta Kanban | Trabajo opcional; estado independiente |
| auditoria | Cambio realizado por la aplicación | Antes/después, fecha, operador y motivo |
| fuentes / origen | Archivo y fila originales | Hash SHA-256, nombre, hoja, número de fila, valores |
| pendientes | Dato que requiere revisión humana | Referencia a origen cuando está disponible |

Los folios se guardan con año. Si en el futuro existen folios de dos áreas con la misma numeración anual, habrá que añadir área emisora/serie a su clave. Para el archivo recibido existe una única correspondencia 833 → 833/2026, proveniente de f833.

La persona puede tener varios legajos y volver a aparecer en otro folio. Los folios, los trabajos y los legajos son conceptos distintos. No se genera una nueva persona por cada aparición.

## Mapeo del Excel real

| Fuente | Destino / decisión |
|---|---|
| bd.Curp, Nombre | personas |
| bd.Folio, legajo | trabajos, relacionados con folios |
| bd.Digitalizador, F_recibido | Digitalizador y recepción del trabajo |
| bd.Fecha_folio | Se preserva; confirmar significado antes de usar como fecha de recepción de folio |
| bd.No_fisicos | Total físico inicial; puede corregirse confirmando bloques |
| bd.Fecha_fisicos, Fecha_digitales, Fecha codificado, C_folder | Hitos históricos conservados y pendientes de revisión, sin inventar intervalos |
| bd.No_digitales | Valor legado preservado; no se mezcla con inventario TIFF verificado |
| bd.Pag | Valor legado preservado; las páginas operativas proceden del último reporte confirmado |
| bd.f_broche | Cantidad fuera del broche, considerada subconjunto del total físico |
| bd.carpetas | Marca histórica 0/1; verificación manual disponible |
| Otros campos de bd | Se conservan en origen; no todos tienen formulario en v0.1 |
| f833 | Miembros de folio 833/2026; no se usa fecha solicitud como fecha de recepción |
| cont.DIV1…DIV50 | Filas de conteos sin límite de 50 bloques nuevos |
| incid | Incidencias abiertas; una acción escrita no demuestra resolución |
| cat_incid | Tipos de incidencia; EXP_2006 repetido pasa a revisión |
| cat_datos | Catálogo de codificación documental, diferente de cat_incid |
| reg_dig | Se conserva como origen; la importación operativa se hace desde el CSV |
| kanban | Tareas de proceso independientes de estados documentales |

Las hojas sin folio se vinculan solo cuando existe un único trabajo coincidente. Si hay varios trabajos, el registro queda pendiente. f833 no indica legajo: para los miembros sin bd se propone legajo 1 y se deja una revisión explícita. La identidad de un trabajo no se edita para no trasladar su historia por error; se desactiva el trabajo erróneo y se crea el correcto.

## Hallazgos verificados en los adjuntos

- bd: 27 filas con CURP. Aunque Excel reporta una dimensión de 1990 filas, las filas de formato vacías no se importan como trabajos.
- f833: 54 filas de miembros. La unión con bd produce 55 trabajos, no 27 ni 54; no se descartan personas presentes solo en una fuente.
- cont: 27 conteos, 97 bloques; no hay discrepancia entre sus sumas y bd en estas fuentes.
- Total No_fisicos de bd: 2027 hojas.
- Catálogos importados: 64 documentos y 7 tipos de incidencia, 71 en total. Una fila duplicada queda conservada para revisión.
- incid: 12 registros. Kanban: 7 tarjetas.
- CSV: 11 ejecuciones, 66 columnas. El adjunto tiene una envoltura adicional de CSV con coma; el importador reconoce este caso concreto y la elimina antes de validar. No se aplica una sustitución general de comillas.
- El nombre escrito por el BAT para páginas es TOTAL_PAG_DIGITALES_CONOCIDAS. No confundir con el nombre de la variable interna del BAT, que incluye PAGINAS.
- Originales, incluidas fórmulas y formatos del Excel, se entregan intactos. El lector solo toma valores almacenados: no recalcula fórmulas. Recalcula y guarda en Excel antes de una importación inicial desde otra copia.

## Estados y fechas

Secuencia: Recibido → Conteo en curso → Conteo completado → Escaneo en curso → Expediente escaneado → Codificación en curso → Expediente codificado → Revisión en curso → Expediente cerrado.

Cada cambio finaliza el intervalo anterior y abre otro con fecha/hora local y zona horaria. Se puede retroceder con motivo; se conserva toda la historia. Las horas provienen del reloj de la PC, que debe ser correcto. No son tiempos efectivos de trabajo: incluyen pausas y esperas.

Al importar, los trabajos comienzan en Recibido como estado técnico provisional. Las fechas históricas quedan en origen y pendientes. No usar estos intervalos iniciales para afirmar cuánto duró el trabajo antes de la importación. No se implementa edición retrospectiva de intervalos en esta versión.

Para llegar a Conteo completado debe existir total físico confirmado. Para cerrar se exige: inventario TIFF de alcance Legajo vinculado, RESULTADO=OK, conteo de páginas COMPLETO, carpetas verificadas y ninguna incidencia abierta. El cierre sigue siendo una confirmación humana de la revisión. No se comprueba automáticamente que cada documento físico tenga imagen ni que los TIFF estén en disco.

## Conteo

Cada bloque se guarda al pulsar Enter. La suma usa solo bloques activos. Corregir o anular conserva bitácora. Confirmar copia la suma a fisicos. Para volver a contar tras avanzar, retrocede a Conteo en curso con un motivo. El total confirmado anterior permanece hasta confirmar el nuevo total.

Supuesto operativo explícito: f_broche está incluido en el total de hojas físicas. No se suma una segunda vez. Si el área define que No_fisicos excluye esas hojas, hay que cambiar esta regla antes de usar el conteo en producción.

Una hoja física puede producir una o dos páginas digitales; un TIFF puede contener varias páginas. Una diferencia no demuestra por sí sola un error. No se utiliza páginas/hojas como porcentaje de integridad.

## Reportes TIFF y deduplicación

Se conserva cada ejecución. La huella del contenido normalizado evita importar la misma fila dos veces, incluso si proviene de otro archivo. La fecha se transforma a formato ordenable; el ID resuelve empates de hora.

El BAT original no proporciona folio, legajo ni identificador de ejecución. Por eso ningún reporte se asigna automáticamente a un trabajo. El usuario debe verificar la ruta, alcance y folio. Si abarca varios legajos, seleccionar CURP completa: se conserva el vínculo de referencia, pero no se reparten ni suman esas métricas por legajo.

Los indicadores toman únicamente la última ejecución válida, confirmada como Legajo, por trabajo. Las métricas MOV_* son movimientos de una ejecución; INV_* es inventario posterior. Sumar inventarios de dos ejecuciones duplicaría existencias. Un archivo no legible no se clasifica como individual y sus páginas desconocidas no se convierten en cero conocido.

Las métricas se validan: archivos individuales+multi+no clasificados; páginas individuales+multi; sumas PERSONALES/FEDERAL; total con raíz; regla 1 página=individual, 2 o más=multi; coherencia del resultado. Las filas rechazadas permanecen en origen y pendientes.

**Limitación del organizador original:** su ruta es CURP/PERSONALES y CURP/FEDERAL; no separa legajos. Tampoco consulta el catálogo editable: DP y FP van a PERSONALES, HL a FEDERAL. Cambiar carpeta en el catálogo no modifica el BAT. No ejecutar ese BAT sobre TIFF mezclados de varios expedientes. Antes de usarlo para dos legajos de la misma CURP debe diseñarse y probarse una separación de carpetas y un reporte v4 con FOLIO, LEGAJO, ALCANCE e ID_EJECUCION. Esta entrega no modifica ni ejecuta esos scripts.

## Indicadores implementados

| Indicador | Regla |
|---|---|
| Trabajos activos | Cantidad de folio/CURP/legajo en filtro |
| CURP distintas | Personas únicas entre esos trabajos |
| Cerrados | Estado Expediente cerrado |
| Avance de cierre | Cerrados / trabajos activos; sin base si denominador cero |
| Hojas físicas confirmadas | Suma de fisicos conocidos |
| Sin conteo confirmado | fisicos nulo; no equivale a cero hojas |
| Con inventario vinculado | Trabajos con al menos un reporte válido de alcance Legajo |
| Archivos TIFF | Suma del último TOTAL_DIGITALES_TIFF por trabajo elegible |
| Páginas conocidas | Suma del último TOTAL_PAG_DIGITALES_CONOCIDAS por trabajo elegible |
| Inventarios parciales | Últimos reportes con conteo diferente de COMPLETO |
| Incidencias abiertas | Incidencias Abierta de trabajos filtrados |
| Gráfica por etapa | Agrupa trabajos según siguiente proceso pendiente |

Filtros: CURP/nombre parcial, folio exacto, estado, digitalizador exacto y rango de fecha de recepción del trabajo. Fechas desconocidas se excluyen al usar rango. Indicadores excluyen inactivos aunque estos se muestren en la lista. Kanban y las tablas administrativas no comparten esos filtros.

Las 66 métricas (PERSONALES/FEDERAL, individuales/multi, archivos/páginas) pueden verse en el detalle del reporte y exportarse en trabajos.csv cuando el reporte está vinculado. No todos tienen gráfica específica en esta primera pantalla.

## Exportación BI

trabajos.csv: una fila por trabajo con datos de su último inventario confirmado. indicadores.csv: los KPI de la vista filtrada. Ambos responden a los filtros activos.

historial.csv, incidencias.csv, catalogos.csv, ejecuciones.csv, pendientes.csv y auditoria.csv: tablas completas, sin el filtro de pantalla. El CSV usa UTF-8 con BOM y punto y coma. Se protegen celdas de texto que empiezan con símbolos de fórmula para abrirlas en Excel.

Modelo BI futuro: dimensión persona, folio, fecha, documento, operador y etapa; hechos trabajo, bloque de conteo, ejecución TIFF, incidencia y transición. En Power Query relacionar por ID interno de trabajo, no solamente CURP. No unir dos tablas de muchos registros directamente y sumar ambos lados: eso multiplica las filas. En el futuro las tasas de productividad requieren fechas confiables, tiempos de trabajo y unidad explícita; la v0.1 no las inventa.

## Evolución de tecnología

Con equipo/OS soportado: instalar Python mantenido y validar esta misma aplicación con una copia de la base. Para acceso simultáneo y permisos: elegir una aplicación web con framework mantenido y PostgreSQL; reutilizar reglas, migrar datos y sustituir la interfaz Tkinter. No se necesita reescribir por el mero hecho de tener mejor hardware.

Versionar migraciones posteriores a schema_version=1, respaldar antes de aplicar cambios de esquema, probar migración sobre copia y conciliar totales. Una elección concreta de versiones de framework, OCR y BI se hará con documentación vigente al momento de migrar.
