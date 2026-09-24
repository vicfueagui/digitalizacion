# Diseño técnico del traslado, formato 1

Kit 0.6.3; código operacional capturado independientemente, normalmente 0.6.2. Núcleo SQLite 7 y TIFF 3. No hay DDL nuevo, actualización de esquema, sustitución de producción ni cambio del dominio funcional en esta fase.

## Arquitectura y responsabilidades

| Límite | Componentes | Responsabilidad |
| --- | --- | --- |
| Interfaz | migrar.py, app/migration_ui.py | Formularios, selección de rutas, progreso en trabajador y confirmación del corte |
| Traslado | app/transfer.py | Inventario de código/datos, exportación, verificación, restauración exclusiva y comparación |
| Aceptación | app/migration_acceptance.py | Ensayo aislado, runtime conservador, evidencia, barrera de activación y arranque |
| Integridad | app/integrity.py | SQLite, FK, todas las tablas, referencias TIFF, hashes, páginas, versiones y operaciones incompletas |
| Portabilidad | app/portability.py | Referencias activas estrictas; historia normalizada solo por prefijos probados |
| Respaldo | app/backup.py | API SQLite backup, inventario y restauración a raíz nueva |
| Filesystem | app/manifests.py, app/workspace.py | Nombres portables, enlaces/junctions, límites de raíz y exclusión entre procesos |
| Recuperación TIFF | app/tiff_recovery.py | Reconstrucción externa de un candidato exacto desde revisión y operación |
| Runtime | app/runtime.py, python_runtime.py | Ejecución real del candidato, perfil y resolución con alternativas |
| Bootstrap Windows | EJECUTAR.bat, ejecutar_python.ps1, lanzar.py | Localización sin depender de PATH, despacho único y propagación del resultado |
| Actualización | actualizar.py, app/update_recovery.py | Operación independiente: resguardo, código anterior, huella de datos y recuperación |

La UI llama servicios; la exportación no construye Store ni ejecuta migraciones. Store sigue siendo el límite del uso operacional. Los servicios de TIFF, versiones y auditoría existentes no se refactorizan ni sustituyen.

## Diferencia entre programa y herramientas

El repositorio local carecía de varias correcciones que el usuario ya aplicó en oficina. Sustituir la producción por esta copia para poder migrar habría añadido una actualización de código a la operación. Por eso `programa/` contiene exactamente el código permitido capturado en origen, con su propio mapa SHA-256; `herramientas/` contiene el kit. Una versión declarada igual no demuestra archivos iguales: se compara contenido.

El inventario usa la lista cerrada de release, más scripts Python/BAT/PowerShell no ocultos en la raíz para conservar resolutores locales. Requiere main, core, workspace, migraciones, esquema, versión y herramientas de prueba. No captura módulos arbitrarios fuera de esos límites. Una instalación con extensiones fuera de la estructura soportada requiere revisar el inventario y ampliar explícitamente el formato antes del traslado.

No se incluyen entornos, caches, configuración con rutas personales, backups anteriores, fuentes externas ni directorios ajenos a datos/reportes. Se mantienen en origen. Sí se conservan TODOS los archivos gestionados en datos/reportes, incluidas entregas y evidencia de importación, no únicamente TIFF activos. Si hay otra base `.db/.sqlite/.sqlite3` en esos árboles, se detiene para clasificarla: no se copia abierta ni se omite silenciosamente.

## SQLite y WAL

El origen se abre mediante URI `mode=ro`. Se usa WorkspaceLock para impedir otro proceso cooperante y se exige cierre operativo de la aplicación. El diagnóstico obtiene snapshot con `Connection.backup`; exportación obtiene otro y prueba equivalencia. `PRAGMA integrity_check` y `foreign_key_check` deben pasar. El snapshot usa journal DELETE y no depende de auxiliares del origen.

`-wal`, `-shm`, `-journal` se identifican por nombre ANTES de resolve/stat. No se silencian PermissionError de documentos incluidos. Los commits todavía presentes en WAL participan en la API de SQLite y en el fingerprint lógico (`iterdump` bajo transacción). No se copian auxiliares físicamente, ni se fuerza checkpoint del origen.

La base y documentos originales no se reescriben. El bloqueo puede crear `.digitalizacion.lock`; SQLite puede abrir sus auxiliares de coordinación. Eso no es una edición de datos ni de auditoría. Se compara estado antes/después y antes de publicar. Una herramienta externa que ignore bloqueos exige la disciplina de cierre; no existe un congelamiento distribuido de dos computadoras desconectadas.

## Huellas y prueba de equivalencia

Se registran dos conceptos diferentes:

- Huella lógica de origen para detectar cualquier cambio entre exportación y comparación del origen congelado, incluyendo WAL confirmado.
- Resumen portable de esquema y todas las tablas: nombres/columnas, número de filas y SHA-256 de filas tipadas ordenadas por su hash. Incluye duplicados, BLOB, float.hex, sqlite_sequence, índices/triggers, auditoría, relaciones y metadata. No depende de orden físico de páginas o de rowid de lectura.

Los hashes de todas las filas protegen contenido y conteos, no solamente cantidades. FK comprueba relaciones. La base SQLite transferida también tiene un SHA físico en el manifiesto. Cada archivo de datos y código tiene otro SHA.

Las normalizaciones autorizadas generan `informes/normalizacion.json` con tabla, ID, campo, antes y después. Sobre OTRA copia temporal se invierten exclusivamente campos permitidos, y se exige identidad del resumen completo con `informes/origen.json`. Cualquier diferencia restante detiene exportación/verificación. La base original nunca recibe esas sustituciones. La huella del SQLite físico exportado puede diferir legítimamente del origen.

SHA-256 ofrece una prueba criptográfica de igualdad de contenido bajo su resistencia a colisiones; no es firma digital ni autenticación. El usuario conserva por separado el SHA del manifiesto final. Verificar con una huella recalculada después de una alteración no ofrece esa protección. La CLI de importación exige `--sha256`; la API admite omitirla únicamente para comprobaciones internas de creación/tests.

## Rutas activas e historia

Activas: archivos_tiff.ruta/original, revisiones_tiff.ruta, versiones_archivo.ruta, entregas.ruta y archivos de sus manifiestos. Se rechazan `..`, escapes, rutas Windows extranjeras en Mac, nombres no portables, symlinks/junctions/reparse points incluso internos. Se verifican existencia y SHA. No se corrige un hash para aceptar otro archivo.

Operaciones completadas: los campos conocidos de primer nivel antes/despues/original/copia/respaldo/source/target/destino/ruta son evidencia. No se exige que sus nombres antiguos existan. Se normalizan en la copia si pertenecen al workspace actual o a un prefijo declarado respaldado por correspondencia con una referencia activa cuyo SHA coincide. No se infiere un workspace solo por encontrar `/datos/` en un texto. Prefijos desconocidos y texto libre quedan intactos. El JSON de auditoría y rutas anidadas de historia no se reescriben indiscriminadamente.

Las operaciones TIFF preparadas, sustituciones sin completar y entregas Preparando/Incompleta bloquean el traslado: no se transporta una reparación a medias como producción correcta.

## Publicación, idempotencia y barreras

Exportar/restaurar construye primero una carpeta temporal hermana. Se verifica todo antes de publicar. La publicación reserva el destino con mkdir exclusivo y mantiene `INCOMPLETO.txt` hasta que todos los archivos se trasladan; retirar esa marca es el último paso. Se evita rename de directorio sobre un destino vacío ajeno, que POSIX permite sobrescribir. Un fallo conserva las marcas y evidencia, nunca una aceptación.

El importador verifica el paquete completo ANTES de crear el destino. No ejecuta código recibido hasta verificarlo. Rechaza archivos sobrantes, ausentes, nombres no portables y manifiestos internos divergentes. Restaurar requiere carpeta inexistente. Repetir indica que ya existe; no fusiona ni sobrescribe. No pretende reanudar automáticamente una copia parcial.

`workspace/.restauracion_incompleta` mantiene bloqueado Store de 0.6.2 después de importar. El ensayo ejecuta la suite del kit, la suite del programa conservado, creación de demo y prueba gráfica. Registra runtime, root, paquete y hash del informe. La aceptación revalida todo y requiere confirmación de corte/revisión visual; retira la marca al final. Un paquete laboratorio no puede habilitar producción.

La comprobación técnica `MIGRACION VERIFICADA` incluye su alcance. Antes de aceptación no significa autorización de captura. Después, el lanzador verifica código/runtime y estado; si un ejecutable se rompe, admite una ruta alternativa con idénticas versiones/capacidades y registra el cambio en evidencia/runtime-*.json; no exige que datos legítimamente nuevos sigan iguales al paquete inicial. La evidencia de la aceptación queda conservada. Mover o actualizar una instalación ya aceptada requiere otra operación planificada; no se cambia silenciosamente su línea base.

## Runtime y BAT

Los BAT de inicio, diagnóstico, pruebas, actualización, instalación y migración comparten EJECUTAR. PowerShell 2.0 sirve únicamente de bootstrap: .venv, configuración literal, variable explícita, registro Windows y lanzador py en rutas conocidas. No busca python a ciegas en PATH. Python confirma ejecución, CPython x64, versión, Tk/Tcl, Pillow y libtiff. Existe fallback si un ejecutable es vacío, inválido, incompatible o no responde. El bootstrap no repite una acción operacional fallida con otro intérprete.

Perfil legado: 3.8.10, Tk8.6, Pillow9.5.0/libtiff. Instalador: mismo Python/Tk, permite Pillow ausente para preparar un entorno local. Laboratorio: CPython x64 con Tk/Pillow/libtiff; solo datos ficticios en migración. En aceptación real se exige Windows10 build entre10240 y21999 y versiones Python/Tk/Tcl/Pillow/libtiff/SQLite iguales al origen. Windows11 y otros sistemas no se certifican como Windows10.

Los scripts citan argv/rutas; no ejecutan texto de configuración como código. No cambian ExecutionPolicy global. Si la política institucional impide PowerShell, el técnico puede ejecutar la CLI con la ruta absoluta del Python comprobado; no se recomienda desactivar controles de la organización.

## Recuperación TIFF con evidencia

`auditar_integridad_tiff.py` y `diagnosticar_integridad.py` producen diagnóstico local legible/JSON. Detectan referencias faltantes, SHA distinto, páginas/bytes de versiones inconsistentes, SQLite/FK y rutas inválidas. Conteos incluyen trabajos, folios, expedientes, originales, actuales, revisiones, versiones, operaciones y auditoría; el resumen abarca además cada tabla existente.

Ejemplo técnico con IDs ficticios, sobre origen cerrado:

```bat
"RUTA\python.exe" auditar_integridad_tiff.py --workspace "D:\Archivo" --salida "E:\Evidencia\candidato-68" --archivo 68 --revision 12 --operacion 83
```

Se exige revisión y operación editar completada para el mismo archivo; original y revisión con SHA válido; coincidencia de página y operaciones entre sus registros. Solo reproduce giros/recortes documentados mediante el editor existente. El candidato externo debe producir EXACTAMENTE hash_actual y páginas esperadas. Si no coincide, no se publica un candidato válido. No sustituye el archivo faltante, no edita SQLite, no cambia hashes, no elimina revisiones. `INCOMPLETO.txt` identifica una copia externa interrumpida.

Esto formaliza un mecanismo de prueba, no una reparación automática. Restaurar el candidato en producción necesita autorización, preservación de evidencia/respaldo verificable y registro de intervención. Cuando la base exige un hash distinto del original, copiar el original sin más destruiría evidencia de la edición. Cambiar versión de Pillow/libtiff puede impedir reproducir los mismos bytes; se conserva el runtime legado.

## Operación técnica y pruebas

Entradas CLI: `migrar.py exportar`, `verificar-paquete`, `comparar-origen`, `restaurar`, `verificar-destino`, `ensayar`, `activar`, `abrir`; usa `--help` en cada una. Sin argumentos abre el asistente. Las salidas de comparación incluyen conclusión y diferencias; estado fallido devuelve código distinto de cero.

Regresiones existentes: actualización interrumpida, retorno de código, rechazo después de captura, WAL confirmado, enlaces/junctions/traversal, rollback de esquema, TIFF individual/multipágina y restore completo. Nuevas: orden de exclusión, historia solo en copia, todos los hashes de referencias, reconstrucción exacta sin reparar, raíz/usuario distintos, manifest externo, publicación interrumpida, activación revalidada, entornos ausentes/vacíos/inválidos y selección del válido.

En Windows se añaden handles nativos que impiden renombrar WAL/SHM y detector de cualquier intento de resolve, prueba PowerShell/BAT con espacios/acentos y .venv de cero bytes, y traslado con SUBST a otra unidad. Mac los omite explícitamente. El ensayo no habilita fuentes privadas externas. Consulta resultados exactos en VALIDACION_V063.md.

## Límites de evidencia y reversión

No hay acceso a las máquinas reales ni a producción. Falta demostrar allí A–M: exportación final, igualdad real, runtime/locking, aceptación visual, rendimiento con 4GB y prueba de rollback antes de capturar. El software no puede evitar una captura deliberada en el Win7 congelado ni una edición manual que retire barreras; el corte queda bajo custodia de la oficina.

Rollback previo a capturas: comprobar origen contra paquete, cerrar destino, volver al origen intacto. Después de capturas: respaldo de estado nuevo y traslado planificado; nunca restaurar lo antiguo encima. No se garantiza que un runtime futuro pueda reconstruir TIFF antiguos byte a byte. No hay modernización productiva, Docker obligatorio ni migración de esquema en esta entrega.

## Trazabilidad de los 24 escenarios obligatorios

| Casos solicitados | Evidencia ejecutable |
| --- | --- |
| 1 WAL confirmado; 2 SHM; 3 WAL bloqueado | test_migration_integrity.HistoricalSafetyTests; test_windows_migration con handles nativos y detector de resolve |
| 4 actualización interrumpida; 5 cambios posteriores | test_continuation, test_update, test_safety; test_transfer.source_commit_after_export |
| 6 activo faltante; 7 alterado; 8 original; 9 revisión; 10 reconstrucción | test_migration_integrity.InventoryRecoveryTests, test_safety y candidato exacto externo |
| 11 activo externo; 12 historia absoluta; 13 traversal | HistoricalSafetyTests y validación común de manifiestos en test_safety/continuation |
| 14 otra raíz; 15 usuario distinto; 16 otra unidad | test_transfer y ensayo completo externo; SUBST exclusivamente Windows |
| 17 sin venv; 18 inválida; 19 selección | test_runtime y bootstrap nativo; fallback después de capturas en test_transfer |
| 20 espacios; 21 Unicode | Fixtures de transferencia/runtime y prueba PowerShell Windows |
| 22 TIFF individual; 23 multipágina; 24 restauración completa | Suite TIFF existente, test_transfer, ensayo_migracion con código0.6.2 conservado y prueba gráfica |

La columna de evidencia indica qué ejecutar; los casos exclusivos de Windows siguen pendientes en el entorno Mac. Los originales/revisiones/versiones se verifican aun cuando el TIFF activo ya no coincida con el original.
