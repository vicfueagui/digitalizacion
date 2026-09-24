# Plan de migración conservadora Windows 7 → Windows 10

Estado inicial revisado: 0.6.2, núcleo SQLite 7, TIFF 3. Fecha: 2026-09-23. Trabajo local con datos inventados; las dos computadoras de oficina no están conectadas a esta sesión. No se certificará su migración con pruebas del Mac.

## Diagnóstico previo al cambio de código

Se inventariaron 61 archivos Python (33 módulos de app, 18 archivos de pruebas, 6 herramientas, 4 entradas), 8.332 líneas, SQL de creación/migraciones, cinco BAT, arranque POSIX, requisitos, manifiestos y documentación. El mapa de imports/definiciones está en `.development/w10-source-map.json`. Dependencia externa funcional: Pillow; resto biblioteca estándar, Tk y SQLite. Base de comparación ejecutada: 231 pruebas, 223 aprobadas, 8 privadas omitidas, 0 fallos/errores en CPython 3.11.4, macOS, Pillow 12.3.0.

La UI se apoya en Store/servicios, con algunas reglas aún en mixins. Workspace delimita archivos y usa bloqueo de proceso. Las migraciones SQL son transaccionales con snapshot previo. Documentos, versiones, originales, revisiones, operaciones y auditoría son mecanismos complementarios; no se sustituirán por un simple inventario de nombres. Las entregas tienen manifiestos inmutables y hashes propios. Se conserva el esquema íntegro.

Backup crea snapshot con la API de SQLite, verifica FK, referencias y hashes; restore requiere destino nuevo. Actualizar conserva código anterior y huella lógica de datos; el retorno se rechaza tras capturas posteriores. El ZIP de release tiene lista cerrada y excluye datos. La suite ya cubre interrupciones de actualización/retorno, WAL confirmado, TIFF, referencias, enlaces, traversal, entidades y estados.

**Diferencias comprobadas con los incidentes reportados:** esta copia NO incluye todavía el resolutor de intérprete operativo mencionado por el usuario; los BAT solo comprueban existencia de .venv. Backup excluye auxiliares antes de resolverlos, pero `data_fingerprint` aún lo hace después. `inventory_files(normalize=True)` trata todas las rutas de operaciones como activas y puede fallar por historia legítima. No existe exportación de migración con comparación y activación. El asistente 0.6.2 exige Windows 7. Son diferencias entre copias, no evidencia de que el equipo del usuario siga fallando.

## Decisiones de alcance

- Migrar conserva **el código exacto de la instalación de origen**, incluidos sus cambios locales permitidos; no lo sustituye por la versión del kit de herramientas. Se registra su propio manifiesto. No se ejecuta código transferido antes de verificar el paquete.
- Herramientas de traslado separadas del programa capturado. El destino guarda programa, workspace y herramientas en carpetas distintas y usa un lanzador que elige explícitamente el workspace.
- Python 3.8.10 x64 / Pillow 9.5.0 continúa en ambas computadoras para la primera migración. No se copia .venv. Un resolutor compartido prueba candidatos de verdad y registra rechazos.
- Exportación no abre Store ni migra esquema. Usa snapshot SQLite, exclusión temprana WAL/SHM y auditoría de todos los archivos requeridos. Una operación TIFF incompleta bloquea exportar.
- Huella de base original y huella portable se distinguen. La comparación verifica esquema, todas las filas y tablas (incluida auditoría), referencias, hashes y conteos. Cambios permitidos de rutas se aplican solamente a la copia y se registran.
- Las rutas activas son estrictas. Las rutas históricas de operaciones completadas se conservan como evidencia; solo se normalizan prefijos inequívocamente vinculados al workspace, con evidencia de correspondencia. No se reescribe arbitrariamente JSON de auditoría ni se arreglan hashes.
- Publicación a carpeta nueva, marcas de incompleta y destino bloqueado hasta verificación automática, ensayo del mismo código en demo y confirmación humana. No habrá una producción aparente tras un fallo parcial.
- La reconstrucción TIFF produce candidatos fuera del workspace, desde revisión/operación comprobadas, y solo se considera válida si obtiene exactamente el hash esperado. No reemplaza automáticamente archivos ni hashes.
- El origen se congela por procedimiento operativo y queda como contingencia. El software local no puede impedir escrituras en otra computadora desconectada: esa limitación se documenta y requiere una sola sede activa.

## Grupos de implementación y comprobación

1. Regresiones de auxiliares bloqueados y rutas históricas; correcciones mínimas compartidas con backup/recuperación. Ejecutar seguridad/continuidad.
2. Inventario de lectura, auditoría TIFF y recuperación de candidato. Probar faltantes, alteración, originales/revisiones, hash exacto y límites de rutas.
3. Resolutor Python compartido, BAT y perfiles explícitos. Probar .venv ausente/vacía/no ejecutable, configuración, alternativas, espacios y Unicode. Ejecutar lo posible localmente y distinguir Windows nativo.
4. Exportar/verificar/restaurar/comparar/ensayar/activar migración con UI y CLI. Capturar código real y datos en formato verificable. Probar WAL, otro nombre de usuario/raíz/unidad simulada, fallos intermedios, adulteración, repetir y comparación de todas las tablas.
5. Manual sencillo Windows 7 → 10, documento técnico, rollback, matriz y deuda/hoja de ruta. Conservar original y paquete verificado; ninguna vuelta atrás sobre capturas posteriores.
6. Suite completa, ventanas con TIFF individual/multipágina y ensayo extremo a extremo con paquetes reales. Registrar versión/plataforma, aprobadas/omitidas/fallidas. Preparar release del kit y manifiesto/SHA-256. Pruebas en Windows 7 y Windows 10 permanecen pendientes hasta recibir sus informes reales.

## Modernización posterior, separada

Se prepara matriz reproducible y candidatos de laboratorio, conservando el perfil legado. La elección de Python moderno se fundamenta en documentación oficial y disponibilidad de wheels/Tk; pruebas de píxeles y de bytes se informan por separado. No se activa un runtime candidato sobre producción desde la migración. Docker es opcional para CI futuro y no se instala ni exige en la HP de 4 GB. OCR, asincronía, configuración, UI/servicios, empaquetado y otra base requieren fases posteriores con sus propios criterios de aceptación.
