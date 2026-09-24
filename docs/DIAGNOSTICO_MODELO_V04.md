# Diagnóstico del modelo 0.4.1 previo a la actualización operativa

Fecha: 2026-09-21. Fuente: código y pruebas de esta carpeta. No se dispone de expedientes originales, Excel privado ni acceso al Windows 7. No hay repositorio `.git`; se conserva el bundle original y las distribuciones anteriores. El documento solicitado define nuevas reglas de negocio; los archivos históricos no las sustituyen.

## Arquitectura encontrada

Tkinter (`ui.py`, `coding_ui*.py`) llama a `Store` (`core.py`) y `CodingService` (`coding.py`, `coding_v3.py`). SQLite y los TIFF viven bajo un `Workspace` explícito, con bloqueo de un operador. `migrations.py` maneja esquema núcleo 2 / TIFF 3, transacciones y snapshot antes de migrar. `backup.py` verifica referencias y hashes; `actualizar.py` distribuye solo código y conserva un resguardo completo. No hay servidor ni autenticación real.

| Tablas | Responsabilidad y limitación actual |
|---|---|
| personas, folios, trabajos | La persona se identifica por CURP; trabajo mezcla identidad CURP/legajo, folio y operación. Un trigger bloquea la misma identidad en otro folio |
| conteos, incidencias, historial, auditoria | Vinculados a ID de trabajo; se pueden conservar como hechos de un ciclo |
| catalogos, atajos, atajos_numericos | Catálogo dinámico con destino PERSONALES/FEDERAL y atajos; reutilizable |
| archivos_tiff, revisiones_tiff | ID entero de registro, hash actual/original y copias de revisiones; faltan UUID documental y versión inmutable |
| operaciones_tiff, sustituciones_tiff, correcciones_tiff | Diarios recuperables y reescaneos; reutilizar en operaciones de archivos |
| ejecuciones, inventario_pendiente | Reportes ligados a trabajo, invalidación y último inventario; no representan entregas inmutables |
| tareas | Kanban manual de tareas auxiliares, separado del proceso documental |
| fuentes, origen, pendientes | Conservación del Excel/CSV importado; no inventar recepción a partir de solicitud |

## Modelo y mapa de migración

- Añadir `expedientes` con UUID y clave única CURP normalizada + legajo. No borrar ni fusionar trabajos antiguos.
- Conservar `folios` como lotes/préstamos y ampliar sus datos de recepción. Añadir `prestamo_items` con validación y custodia propias. Conservar desconocidos como pendientes, sin atribuir recibos, firmas ni devoluciones.
- Reutilizar `trabajos.id` como ID de ciclo, agregando relaciones al maestro y al elemento de préstamo. Conservar todas las FK de conteos, incidencias, TIFF y auditoría. Sustituir la prohibición global de repetir CURP/legajo por la unicidad del maestro; otro folio permite otro ciclo.
- Agregar historial de asignaciones, calidad y metadatos de tarjeta. Las asignaciones antiguas conservan fecha de inicio desconocida.
- Añadir documentos lógicos y versiones de archivo, sin reubicar TIFF durante la migración. Los enlaces antiguos conservan ID/rutas y se complementan con identidades nuevas; datos dudosos quedan por conciliar.
- Añadir entregas y elementos relacionados, validaciones, sesiones y observaciones con historial. JSON solo para snapshots complementarios; relaciones críticas mediante FK.
- El Kanban será una proyección del ciclo y sus observaciones. Las tareas anteriores permanecen disponibles como tareas auxiliares.

## Riesgos y decisiones

No es posible inferir que un trabajo viejo equivale a una recepción validada, préstamo devuelto o aprobación de calidad. Vincular la identidad normalizada no fusiona conteos, archivos ni eventos de sus ciclos; los duplicados históricos se señalan para conciliación. No inferir el nombre original de un TIFF si no se conserva evidencia fiable. No abrir ni normalizar documentos durante la migración estructural; la validación posterior debe comprobarlos antes de entregar.

Se conservan los nombres y rutas gestionados antiguos. Las entregas nuevas usan nombres canónicos con código, secuencia e ID, en carpetas nuevas por versión, nunca sobrepuestas. El SHA-256 verifica contenido, no identifica el documento lógico. Se conserva el perfil legado y no se agregan dependencias.

## Plan

Fase 0: baseline, copia y diagnóstico. Fase 1: maestro/préstamo/ciclo y asignación. Fase 2: identidad/versiones TIFF. Fase 3: validación/entregas/diff. Fase 4: revisión/observaciones. Fase 5: legado en solo lectura/adopción. Fase 6: 360/Kanban/interfaz. Fase 7: exportaciones, documentación, regresión y paquete. Cada fase se registra en la bitácora.

Baseline ejecutado: 122 pruebas, 114 aprobadas, 0 fallidas/errores y 8 omitidas por fuentes privadas. Evidencia local: `.development/baseline-modelo-operativo.json`.
