# Validación de Digitalización 0.5.0

Antecedente de la entrega anterior. Resultados actuales: [VALIDACION_V06.md](VALIDACION_V06.md).

Fecha: 2026-09-22. Implementación de modelo operativo y ampliación solicitada de respaldo WAL/SHM y UX de Codificación. Solo datos ficticios. La instalación productiva y sus documentos no se modificaron desde este Mac.

## Resultados ejecutados

| Comprobación | Resultado y evidencia local |
|---|---|
| Suite final, CPython 3.11.4 / Pillow 12.3.0 | **181 ejecutadas, 173 aprobadas, 8 omitidas, 0 fallos, 0 errores**. `ensayos/modelo-operativo-v05-final/pruebas.json` y `pruebas.log` |
| Suite final, CPython 3.11.4 / Pillow 9.5.0 | **181 ejecutadas, 173 aprobadas, 8 omitidas, 0 fallos, 0 errores**. `.development/pillow95-entrega-v05.json` |
| Ensayo completo en Mac | Demo, diagnóstico, respaldo, verificación, restauración, diagnóstico restaurado, conservación de SQLite al respaldar y ventanas correctos. `ensayos/modelo-operativo-v05-final/resultado.json` |
| Tk real | App/visor/360/préstamo/Kanban/entregas; 860, 1024 y 1366 píxeles; herramientas adaptables, tres vistas, Ctrl+rueda, miniaturas virtuales con 240 filas, caché acotada, cancelación de edición. `ventanas.log`, `.development/smoke-ux-v05.log` |
| Gramática Python 3.8 | 46 archivos Python distribuibles analizados con AST `feature_version=(3,8)`, ejecutado desde Python 3.11.4. `.development/gramatica-v05.json` |
| Migración antigua | Cinco pruebas con esquema núcleo 1/TIFF 2 sintético: IDs/relaciones/hash, idempotencia UUID, rollback tras reconstrucción, columnas desconocidas y primera edición conservando versiones. `tests/test_model_migration.py` |

Las ocho omisiones pertenecen a `SourceTests`, que requiere Excel/CSV privados originales y autorización explícita. No se habilitaron ni se contaron como aprobadas. Se usan fixtures Excel/CSV sintéticos. Las pruebas de symlink pueden añadir omisiones justificadas en Windows si faltan privilegios; deben leerse en el resultado de ese equipo.

## Corrección de los errores reportados en Windows

`create_backup` comprobaba `plain_path` antes de excluir auxiliares SQLite. Windows puede bloquear `digitalizacion.sqlite3-shm`; ahora la exclusión por nombre ocurre antes de resolver o consultar atributos. La modificación no sustituye el snapshot API SQLite por una copia del archivo abierto ni relaja las comprobaciones de los archivos incluidos.

Las pruebas `test_wal_committed_data_also_blocks_recovery` y `test_backup_wal_and_corruption_refused` pasan en ambos perfiles locales y siguen habilitadas. Se añadieron:

- `test_sqlite_sidecars_excluded_before_resolving_locked_paths`: simula PermissionError si se intentara resolver WAL/SHM/journal, exige que no se consulten, verifica transacción confirmada y documento incluido en el respaldo.
- `test_permission_error_on_included_file_still_stops_backup`: exige que un error de acceso real conserve el fallo y la marca de respaldo incompleto.

La simulación reproduce la condición relevante de orden de exclusión. **No es ejecución real en Windows 7**. Deben pasar allí las mismas pruebas, sin omitirlas ni silenciar PermissionError.

## Cobertura de las 40 aceptaciones del documento

Los nombres siguientes remiten a pruebas dentro de `tests/`; los escenarios nuevos se ejecutan junto con la regresión anterior.

| N.º | Escenario | Evidencia |
|---|---|---|
| 1 | Mismo maestro en nuevo folio/ciclo | `test_operational`: `test_same_identity_new_folio_reuses_master_new_cycle` |
| 2 | Otro legajo, otro maestro | `test_legajo_two_is_separate_master` |
| 3 | 20 elementos y recepción parcial | `test_twenty_items_partial_receipt_and_no_false_acceptance`; extras no relacionados y altas que reabren recepción |
| 4 | Reasignación con historial | `test_reassignment_keeps_history_and_collaboration` |
| 5 | Cierre digital y préstamo abierto | `test_custody_is_independent_of_process`; `test_delivery`: `test_explicit_response_validation_and_approval_leave_loan_open` |
| 6 | Igual nombre, diferente contenido | `test_assets`: `test_distinct_content_same_source_name_preserved` |
| 7 | Igual hash no borra evidencia | `test_explicit_duplicate_adoption_preserves_both`; `test_duplicate_content_is_warning_and_not_deleted` |
| 8 | Reescaneo conserva documento | `test_rescan_links_same_document` |
| 9 | Renombrar conserva UUID | `test_rename_keeps_logical_and_binary_ids` |
| 10 | Retiro excluye próxima entrega | `test_retirement_restore_retains_identity_and_history`; `test_clean_v2_excludes_removed_and_keeps_v1_intact` |
| 11 | Restauración trazable | `test_retirement_restore_retains_identity_and_history` |
| 12 | v1 A/B/C → v2 A/C/D | `test_delivery`: `test_clean_v2_excludes_removed_and_keeps_v1_intact` |
| 13 | Diff retirado/agregado | Mismo escenario y `test_rename_not_added_and_removed` |
| 14 | Exportar no modifica v1 | `test_export_is_new_independent_and_verifiable_without_database` y caso A/B/C |
| 15 | No mezclar ni dejar residuos | Casos anteriores; `test_copy_failure_never_publishes_or_merges_retry` |
| 16 | Cambio invalida validación | `test_external_edit_makes_validation_obsolete_and_preserves_export` |
| 17 | Observación por TIFF/página | `test_observation_page_scope_and_history` |
| 18 | Corregir y publicar v2 | `test_explicit_response_validation_and_approval_leave_loan_open` |
| 19 | Resolución explícita | `test_edit_does_not_resolve_observation`; respuesta/validación/aprobación |
| 20 | Reporte compara v1/v2 | `test_reporting`: `test_final_360_contains_loan_history_manifest_and_changes` |
| 21 | Carpeta correcta | `test_legacy`: `test_valid_folder_readonly_and_snapshot_does_not_adopt` |
| 22 | TXT advertido/no adoptado | `test_txt_warns_and_is_never_adopted` |
| 23 | Código inexistente/inactivo | `test_unknown_and_inactive_codes_fail_preflight` |
| 24 | Código en carpeta incorrecta | `test_correct_code_wrong_folder_detected` |
| 25 | Igual nombre/diferente hash | `test_same_name_different_content_collision` |
| 26 | Duplicado por hash | `test_same_content_different_names_preserved_in_adoption` |
| 27 | Ilegible conserva páginas desconocidas | `test_unreadable_pages_remain_unknown` |
| 28 | Preflight/análisis no modifica fuente | `test_valid_folder_readonly_and_snapshot_does_not_adopt` |
| 29 | Adopción verifica origen/destino | `test_adoption_hashes_match_and_source_unchanged`; cambio de fuente y reanudación parcial |
| 30 | Etapa cambia tarjeta | `test_reporting`: `test_process_actions_update_card_without_drag` |
| 31 | Observación deriva Correcciones | `test_observation_and_resubmission_control_column` |
| 32 | Respuesta deriva nueva revisión | Mismo escenario |
| 33 | Nota/prioridad sin mover etapa | `test_operational`: `test_note_priority_does_not_change_stage` |
| 34 | 360 recién recibido sin cifras inventadas | `test_received_360_has_no_invented_digital_metrics` |
| 35 | 360 final con toda la evidencia | `test_final_360_contains_loan_history_manifest_and_changes` |
| 36 | KPI activo sin sumar snapshots | `test_kpi_counts_active_inventory_not_snapshots`; datasets relacionales y denominador vacío |
| 37 | Sintaxis Python 3.8 | AST de 46 archivos; ejecución CPython 3.8.10 pendiente |
| 38 | Semántica de nombres sin distinguir mayúsculas | `test_safety`: `test_no_overwrite_on_case_collision_or_concurrent_target`, `test_paths_windows_accents_traversal_absolute` y casos de manifiesto |
| 39 | TIFF multipágina conserva páginas | `test_coding`: `test_stream_edit_keeps_other_pages_and_dpi`; `test_assets`: `test_edit_creates_new_immutable_version_keeps_other_pages` |
| 40 | Regresión y reglas sustituidas justificadas | Suite completa; bitácora Fase 1 y cierre 0.5.0 |

También se comprueban corrupción de manifiesto, archivos extra, aprobación con inventario cambiado, permisos de rol en servicios, backups de versiones/entregas, cortes en importación/edición/reescaneo/organización y restauraciones incompletas.

## Reglas anteriores ajustadas

La prohibición de repetir CURP/legajo entre folios se sustituyó por maestro reutilizado y ciclo nuevo. Ya no se cambia el folio de un ciclo sobre el mismo ID. Los reportes legados se etiquetan declarados y no equivalen a archivos gestionados. Un reporte CSV y sus conteos no bastan para cerrar: se requiere entrega y aprobación. Las pruebas se actualizaron por esos cambios de negocio; no se retiraron casos para ocultar fallos. Las pruebas privadas siguen pendientes de sus fuentes originales.

## Límites y comprobación humana pendiente

Windows 7 SP1/CPython 3.8.10 x64, junctions reales, teclado español/numérico, escalado de pantalla y rendimiento con TIFF grandes en 3 GB requieren el [ensayo de oficina](ENSAYO_OFICINA.md). El segundo perfil Pillow utiliza Python 3.11 y macOS; no reproduce el sistema operativo Windows. Se intentó una captura de pantalla local, pero solo devolvió el fondo de escritorio: no se usa como evidencia de inspección visual. Las comprobaciones Tk verifican ventanas/widgets/interacciones y geometría; la comodidad visual final debe revisarse en la pantalla real.

No se acreditan autenticación, multiusuario ni firma digital. Las versiones y entregas ocupan espacio adicional; no hay purga automática. La migración no inventa fechas/recepciones ni resuelve por sí sola la identidad de registros históricos ambiguos. Las fuentes históricas externas quedan fuera del respaldo gestionado hasta adoptarse.

Pasos manuales locales: [OPERACION_V05.md](OPERACION_V05.md). Traslado protegido: [WINDOWS7.md](WINDOWS7.md). Respaldo/retorno: [RESPALDOS.md](RESPALDOS.md). Arquitectura: [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md).

## Paquete y actualización ensayada

`dist/Digitalizacion-0.5.0-codigo.zip` contiene 88 archivos permitidos más `release-manifest.json`; su `.sha256` adyacente identifica la entrega. El build y la comprobación de contenido excluyen SQLite, TIFF, fuentes personales, resultados, demos, `.venv` y resguardos. El manifiesto contrasta cada archivo con el código actual.

El ensayo `.development/e2e_v05.py` pasó con código 0.3 archivado y datos completamente inventados en rutas con espacios: comprobar/aplicar paquete, SQLite byte por byte intacto durante sustitución de código, recuperación previa, reaplicación, migración conservando IDs/legajos/conteo/TIFF multipágina y UUID, FK íntegras, entrega verificable, y recuperación posterior rechazada por cambio de datos. Registro `.development/e2e-v05.log`. El ZIP 0.4.1 anterior permanece intacto. Esto valida el procedimiento local y no reemplaza el ensayo en Windows ni el cotejo de la información productiva.
