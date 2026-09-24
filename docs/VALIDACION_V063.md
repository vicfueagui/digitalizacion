# Evidencia de validación del kit 0.6.3

Fecha: 2026-09-23. Datos exclusivamente ficticios. No se ha accedido a la producción Windows 7 ni a la HP Windows 10. Las pruebas locales no completan la certificación física A–M solicitada; preparan un procedimiento para obtenerla.

## Revisión previa y cambios

Se inspeccionó la versión local0.6.2: 61 archivos Python, esquemas SQL, BAT, backup/restore/update/recovery, TIFF, manifiestos y documentación. Antes de cambios:231 pruebas,223 aprobadas,8 privadas omitidas. Plan previo en PLAN_MIGRACION_WINDOWS10.md; mapa local en .development/w10-source-map.json. No existe metadata .git en esta carpeta: la entrega se identifica mediante manifiesto/SHA, no mediante un commit inventado.

Se corrigieron exclusión temprana de auxiliares en fingerprint, separación historia/activos y detección real del runtime. Se añadieron inventario, recuperación de candidato exacto, formato de exportación/restauración, comparación all-table, barreras de ensayo/aceptación, asistentes y documentación. Sin cambio de esquema ni modernización operacional. El código de origen se conserva separado del kit.

## Suite completa disponible

| Python real | Plataforma | Pillow | Total | Aprobadas | Omitidas | Fallidas | Errores |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CPython3.8.10 x64, conda-forge | macOS11.7.11 Intel / Darwin20.6.0 | 9.5.0 | 276 | 264 | 12 | 0 | 0 |
| CPython3.13.15 x64, conda-forge | macOS11.7.11 Intel / Darwin20.6.0 | 12.3.0 | 276 | 264 | 12 | 0 | 0 |
| CPython3.11.4 x64, entorno existente | macOS11.7.11 Intel / Darwin20.6.0 | 12.3.0 | 276 | 264 | 12 | 0 | 0 |

Ejecuciones: `.development/w10-full3810-final.json/.log`, `.development/w10-full31315-final.json/.log`. También se ejecutó `.development/w10-full3114-final.json/.log`. Los JSON registran también runtime. El perfil3.11.4 usa SQLite3.42.0/Tcl8.6.12. Entorno legado local: Tcl8.6.13, SQLite3.46.0, libtiff4.5.0. Candidato: Tcl8.6.13, SQLite3.53.4, libtiff4.7.1. No son los binarios/librerías oficiales de Windows y no se presentan como tales.

Las12 omisiones son8 pruebas de fuentes privadas no disponibles,2 bloqueos nativos Windows WAL/SHM,1 bootstrap PowerShell/BAT con .venv inválida y1 traslado a otra unidad con SUBST. En Windows podrían variar omisiones por privilegios de enlaces; revisar nombres/motivos, no solo totales.

En la primera ejecución3.8.10 falló una prueba antigua que suponía ausencia de un intérprete compatible. Ahora existe uno de verdad. Se corrigió el fixture para declarar candidatos inexistentes explícitamente; no se omitió el caso ni se relajó el resolutor. La segunda ejecución completa pasa.

## TIFF entre runtimes

`tools/tiff_compat.py` creó cuatro referencias con3.8.10/Pillow9.5.0: giro individual, giro multipágina, recorte y giro fino. Al repetir desde3.13.15/Pillow12.3.0:

- Píxeles, páginas y metadata comparada:4 de4 iguales.
- Bytes y SHA-256:0 de4 iguales.

La comparación devuelve código2 por diferencia real de bytes; no es un resultado aprobado de equivalencia histórica. Evidencia local: `.development/tiff-compat-31315/comparacion.json`. Corpus limitado; no certifica metadata no incluida ni todos los escáneres. **No habilitar Pillow moderno para reconstruir cadenas históricas que exigen los bytes de9.5.**

## Ventanas y aceptación local

La prueba gráfica de aplicación/visor pasó con3.8.10/Pillow9.5.0. El asistente de migración abre, completa una auditoría ficticia desde su trabajador y mantiene visibles sus controles en900x730 y1024x768. Logs: w10-smoke3810.log, w10-smoke-migration.log y w10-smoke-migration-worker.log.

Con3.13.15/Pillow12.3.0 la prueba gráfica completó sus comprobaciones y devolvió0, pero emitió `ValueError: seek of closed file` desde el cierre/finalización de AppendingTiffWriter. Se conserva el log w10-smoke31315.log. Se registra como incidencia pendiente del candidato, no como interfaz moderna libre de problemas. No se modifica el escritor TIFF legado dentro de esta migración para ocultar ese mensaje.

## Ensayo de traslado conservando 0.6.2

Se usa el ZIP0.6.2 anterior con SHA-256 `65a4653f8cf3a8948589a3c82c67daaf6026a2bc193ea6c5dc38fc8bd1e3ed0b`, extraído fuera del repositorio, y una demo creada por ese mismo código. `tools/ensayo_migracion.py` exporta, compara origen, restaura bajo otro usuario/ruta, verifica, ensaya ambas suites, habilita exclusivamente laboratorio y abre el código conservado sobre la demo restaurada con TIFF individual/multipágina. Resultado ejecutado: MIGRACION VERIFICADA para laboratorio, código conservado0.6.2, base de origen idéntica byte a byte, apertura de la demo restaurada y ambas clases de TIFF correctas. Suite del programa conservado:231 totales,223 aprobadas,8 privadas omitidas,0 fallos/errores. Informe: `/Users/admin/PruebasDigitalizacionMigracion/ensayo-conservador-001/resultado.json`; log local `.development/w10-e2e001.log`. El kit capturado en ese ensayo incluía275 tests; la comprobación final de276 incluye además fallback de intérprete tras nuevas capturas.

## Aceptación pendiente en las dos computadoras

| Criterio | Prueba local disponible | Evidencia real que falta |
| --- | --- | --- |
| A–C exportar sin editar, manifiesto, copia portable | Tests y ensayo ficticio | Exportación final Win7, SHA externo y comparación del origen congelado |
| D–G restaurar raíz nueva, rutas, SQLite, TIFF/hashes | Tests con raíces/acentos, all-table, integridad | Ejecutar importación Win10 y los4 casos nativos Windows |
| H–I abrir aplicación/TIFF de1 y varias páginas | Prueba gráfica Mac con legado | Abrir demo y luego copia real en HP; teclado y memoria4GB |
| J–K entidades, auditoría/historial | Conteos más hashes de todas las filas, originales/revisiones/versiones | Comparación real con manifiesto de oficina y revisión por operador |
| L rollback | Origen sin cambios y procedimiento documentado | Ensayar retorno antes de capturar y conservar informes |
| M modernización separada | Perfil candidato aislado, diferencias TIFF registradas | Resolver incidencias del candidato y probar Windows antes de otra release |

No se declara terminada la migración de producción hasta obtener esas evidencias. La etapa de preparación del repositorio sí entrega herramientas y pruebas reproducibles. No hay Docker requerido, cambios de esquema, edición de hashes productivos ni datos reales en el paquete de código.
