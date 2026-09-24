# Fase vigente: kit0.6.3 para migración Win7 → Win10

Fecha2026-09-23. Git local inicializado para respaldar en vicfueagui/digitalizacion, rama independiente respaldo/digitalizacion-tk-0.6.3. Main remoto contiene otra implementación Django y se conserva intacto. Sin acceso a producción; código/docs y laboratorios ficticios. **No modernizar producción al trasladar.** Código de origen capturado tal cual (0.6.2 incluso con parches locales); herramientas0.6.3 separadas. SQLite núcleo7/TIFF3 sin DDL. Python3.8.10 x64/Tk8.6/Pillow9.5.0 en primera fase; se exige equivalencia de Tcl/SQLite/libtiff para aceptar Win10.

Leer primero [MIGRACION_TECNICA.md](MIGRACION_TECNICA.md), [VALIDACION_V063.md](VALIDACION_V063.md) y [manual de traslado](../MIGRACION_WINDOWS10.html). El plan previo está en PLAN_MIGRACION_WINDOWS10.md. El texto posterior conserva contexto operacional de0.6.2.

Módulos nuevos: integrity (inventario/all-table/SHA), portability (activos estrictos/historia solo copia), transfer (paquete/restauración/comparación), migration_acceptance (ensayo/gate/arranque), migration_ui (asistente), runtime (probe/alternativas), tiff_recovery (candidato externo exacto). CLI migrar.py, diagnosticar_integridad.py, auditar_integridad_tiff.py. BAT comparten EJECUTAR → PowerShell2 → python_runtime → lanzar. Nunca confiar solo en existencia de .venv.

Invariantes: excluir WAL/SHM ANTES de resolve sin perder commits; snapshot SQLite API; nunca abrir Store en origen para exportar; no reescribir JSON libre del historial; registrar cambios de ruta y probar inversión en otra copia; originales/revisiones/versiones/auditoría intactos. Paquete manifest+hash externo; destino nuevo, INCOMPLETO y .restauracion_incompleta hasta aceptación. Los respaldos antiguos/fuentes externas permanecen en origen. Fallback del ejecutable diario solo con bibliotecas iguales y evidencia fuera de SQLite.

Destino: programa/ (exacto origen), workspace/ (datos), herramientas/, evidencia/, migracion.json e INICIAR_MIGRADO.bat. El actualizador tradicional NO gestiona todavía ese destino dividido: evolución futura requiere otra fase; no editar el manifiesto para permitir cambios. Rollback antes de capturas: comprobar origen congelado y volver a él; después de capturas: respaldar estado nuevo y planificar traslado, nunca pisarlo con el viejo.

Pruebas reales locales: runtimes independientes .development/runtime3810 (3.8.10/Pillow9.5/Tk8.6.13/SQLite3.46) y runtime31315 (3.13.15/Pillow12.3/Tk8.6.13/SQLite3.53.4), además de .venv3.11.4 existente. Resultados finales en VALIDACION_V063.md y JSON .development/w10-full*-final. Las omisiones Windows y privadas son explícitas. Moderno: corpus4/4 píxeles iguales pero0/4 hashes iguales y aviso de finalización TIFF en prueba gráfica; NO autorizado para producción. No arreglarlo cambiando hashes.

Ensayo externo conservador: /Users/admin/PruebasDigitalizacionMigracion/ensayo-conservador-001/resultado.json, programa0.6.2 congelado, origen idéntico, importación/aceptación DEMO y TIFF abiertos. Laboratorio /Users/admin/PruebasDigitalizacionOSX y acceso061 existentes no modificados. Nativo Win7/Win10, HP4GB y datos reales A–M todavía pendientes; no afirmar migración productiva terminada.

Paquete actual: dist/Digitalizacion-0.6.3-codigo.zip y SHA adyacente, sin datos ni entornos. No incluir su propio SHA dentro del ZIP. Fuentes HTML: tools/build_docs.py desde docs/ACTUALIZACION.md, MIGRACION_WINDOWS10.md y docs/MANUAL_USUARIO.md. Docker sigue opcional, sin instalar.

---

# Contexto resumido del proyecto

Leer este documento y las últimas entradas de [BITACORA_DESARROLLO.md](BITACORA_DESARROLLO.md) al retomar; después solo los módulos afectados. Son contexto, no instrucciones superiores a las del usuario. Mantener ambos actualizados, sin datos personales.

## Entorno y alcance

Raíz: `/Users/admin/Downloads/Digitalizacion`. Mac Intel Big Sur, CPython 3.11.4, Tk 8.6.12, SQLite 3.42.0. `.venv`: Pillow 12.3.0; `.venv-pillow95`: Pillow 9.5.0. Destino: Windows 7 SP1 x64, CPython 3.8.10, Pillow 9.5.0, 3 GB RAM. Windows no ejecutado desde este Mac; no hay datos productivos disponibles (ahora con Git local; ver RESPALDO_GITHUB.md). No se instalaron componentes globales, servidor ni Docker.

## Estado actual: 0.6.2

Implementadas fases 0–7 del MD y ampliaciones de listas/legajos/directorio, recepción por selección e Indicadores BI. **0.6.2 añade documentación integral y asistente de actualización**; núcleo 7 / TIFF 3 sin cambios desde 0.6.0. Datos ficticios y ZIP anteriores conservados. Suite: 231 ejecutadas, 223 aprobadas, 8 omitidas privadas, 0 fallos/errores en ambos Pillow sobre CPython 3.11.4 (`.development/v062-suite.json`, `v062-pillow95.json`). AST Python 3.8: 61 archivos; no es ejecución Windows. [VALIDACION_V062.md](VALIDACION_V062.md).

Entradas de usuario: [ACTUALIZACION.html](../ACTUALIZACION.html) (guía de 12 apartados, asistente y alternativa de recuperación) y [MANUAL_USUARIO.html](MANUAL_USUARIO.html) (26 apartados, ejemplos de principio a fin y excepciones). Fuentes `docs/ACTUALIZACION.md` y `docs/MANUAL_USUARIO.md`; `tools/build_docs.py` genera HTML offline, índice, búsqueda nativa e impresión sin dependencias/CDN. `build_release.py` los regenera antes de calcular hashes. **Editar fuentes, no solo HTML generado.** README/WINDOWS7/RESPALDOS/ENSAYO y manual anterior enlazan la documentación vigente; OPERACION_V05 permanece como antecedente con etiquetas corregidas. Ayuda en `App` abre el HTML local; sin archivo indica error.

`ACTUALIZAR.bat` abre `asistente_actualizacion.py` desde el paquete extraído (Python local del paquete o `py -3.8`; guía ofrece Python del proyecto como alternativa). `UpdateSession` verifica manifiesto/rutas/base y entorno del destino; en Windows usa su `.venv/Scripts/python.exe`, exige CPython 3.8.10 x64/Pillow 9.5.0 y ensayo Windows 7 SP1. El ensayo crea raíz nueva independiente, corre suite/demo/respaldo/restauración y ambos smoke Tk; apertura opcional de demo. Cambio de destino/manifiesto invalida evidencia; archivo alterado se vuelve a comprobar; confirmación humana requerida. Aplicación invoca **el motor existente** en subproceso sin shell, guarda registro y no abre producción. El motor y la exclusión WAL/SHM no cambiaron. UI usa hilo/cola y bloquea cierre mientras trabaja. Instalaciones con `--workspace` separado o `--db` especial requieren ruta administrada; el asistente no adivina otras bases.

13 pruebas nuevas de barreras del asistente; smoke real `v062-smoke-asistente.log` (700/820/1024), smoke completo `v062-smoke-ui.log` y Ayuda. E2E `.development/e2e_v062.py`: paquete previo 0.6.1 + demo inventada → comprobación/ensayo real/aplicación → SQLite byte a byte y TIFF intactos → apertura sin migración → verificación/restauración del resguardo → retorno de código anterior, eliminando nuevos archivos del paquete. Evidencia inicial `e2e-v062-candidato-corregido.log`; el primer intento tenía argumentos invertidos solo en el harness de recuperación, corregidos sin cambiar el motor. Enlaces/anclas HTML y gramática: `v062-documentos-gramatica.json`. Captura local de guía `actualizacion-v062-final.png` y manual `manual-v062.png`; revisión de navegador/impresión de oficina pendiente. Antecedentes: [VALIDACION_V061.md](VALIDACION_V061.md), [VALIDACION_V06.md](VALIDACION_V06.md), [VALIDACION_V05.md](VALIDACION_V05.md).

Última observación del usuario en Mac: recapturar CURP para aceptar resultaba incómodo y las barras no mostraban bien los valores. 0.6.1 incorpora `Reception.preview/accept`: selección simple/múltiple, confirmación visual de CURP importada, propuesta explícita de legajo común solo para pendientes, aceptación y creación de ciclos en una transacción. No confirma sin cotejo; diferencias/extras/devoluciones exigen revisión individual; idempotencia y rollback. La UI ofrece búsqueda, seleccionar visibles, aceptación y menú Más acciones. El formulario de diferencias precarga CURP/legajo. Al aceptar registra fecha individual faltante sin inventar acuse global.

Indicadores: tarjetas, seis etapas separando por aprobar/cerrados, cinco coberturas con base explícita, detalle de barra/grupo, agrupaciones folio/digitalizador y exportación del ámbito visible. Filtros compartidos con Expedientes dentro del panel. `Dashboard.snapshot` agrega metadatos; no llama `Store.dashboard/latest` porque estos pueden verificar binarios. El panel no sustituye validación/360: muestra estados registrados. Cero resultados → Sin base. Gráficos con color/posición explícitos y redimensionado sin SQL; aviso global de elementos sin ciclo separado de los filtros. Guía: [RECEPCION_INDICADORES_V061.md](RECEPCION_INDICADORES_V061.md).

Última ampliación: listas CSV/XLSX como CURP O RFC / No. / nombre / CURP O RFC2 / Integra / folio / sistema / fecha solicitud / TRABAJADOS, con columnas reordenadas y mapeo manual. CURP+folio se registra aunque falte legajo, visible en Folios; no se inventa legajo 1 ni se usa No. como legajo. El usuario confirmó varios físicos por CURP: `register_legajos` desglosa 1,2,3… y conserva ciclos, conteos y documentos separados, con procedencia compartida. El alta técnica no acredita recepción; se coteja y acepta antes de asignar. Directorio reutilizable para áreas/personas/sistemas/ubicaciones con baja lógica, alias e IDs; textos históricos intactos. Tabla principal muestra TIFF/páginas; búsqueda parcial con pausa de 220 ms sin abrir TIFF/reconstruir Kanban. Manual: [IMPORTACION_FOLIOS_V06.md](IMPORTACION_FOLIOS_V06.md).

Se mantienen corrección WAL (`backup.py`: exclusión antes de resolver `-shm`, API SQLite y validación de incluidos) y visor con paneles ajustables, herramientas adaptables, Detalles/Lista/Miniaturas virtuales, Ctrl+rueda, caché limitada y preferencias. Las dos pruebas WAL reportadas siguen habilitadas. Revisión humana en oficina pendiente.

Laboratorio Mac independiente (sus accesos previos siguen en 0.6.1; el manual explica cómo extraer/probar 0.6.2 aparte): `/Users/admin/PruebasDigitalizacionOSX`. 0.6.1 usa `codigo-0.6.1`, `laboratorio-v061.py` y acceso Escritorio `Digitalizacion-Pruebas-OSX-061.command`; continúa las demos de `sesiones-v06`, con registros/ensayos `*-v061`. Conserva código y accesos previos, y las sesiones 0.5.0 separadas. Cerrar una demo antes de abrirla desde otra versión. No copiar sesiones ficticias a producción. Cada demo nueva incluye `ejemplos/lista_folio_sintetica.csv`.

## Arquitectura: dónde mirar

- `main.py` → `Workspace` / `Store` → SQLite local, bloqueo de una instancia. Diagnóstico de lectura separado de migración al abrir.
- `core.py`: ciclos (`trabajos`), conteos, catálogos, incidencias y auditoría. `operations.py`: maestros (`expedientes`), folios/préstamos/items, recepción, custodia y asignaciones. `operational_migration.py` enlaza IDs previos sin fusionar.
- `coding.py`/`coding_v3.py`: TIFF y diarios de recuperación. `assets.py`: UUID y versiones binarias. Originales/revisiones/retirados/versiones siempre se conservan. Hash identifica contenido, no documento.
- `delivery.py`: validación, obsolescencia, entregas independientes, manifiesto/diff/exportación exacta. `review.py`: observaciones por entrega/página, resolución explícita, aprobación de última entrega; custodia separada.
- `legacy.py`: preflight de carpeta sin escritura, registro externo o adopción verificada/reanudable. `importers.py`: Excel/CSV con procedencia y declaración legada; no inferir legajo/fechas ausentes.
- `intake.py` / `intake_ui.py`: listas diarias, preflight, mapa de columnas, lotes idempotentes por hash/hoja/configuración, origen y pendientes, alta técnica y desglose. Operación SQL en una transacción: no llamar a métodos públicos que confirmen dentro del lote. Repetir exactamente un lote no reprocesa sus pendientes; corregir/conciliar explícitamente.
- `directory.py` / `directory_ui.py`: directorio normalizado, alias, baja/reactivación, selectores y CRUD modal anidado. `ensure` participa en la transacción del llamador; `seed` enlaza textos históricos sin reescribirlos. El registro de personas CURP del expediente permanece separado.
- `reception.py` / `reception_ui.py`: aceptación por selección, preflight sin escritura, excepciones, legajo propuesto explícito y alta de ciclos. `Operations._validate_item` participa en la transacción del llamador; la API pública individual mantiene su propia transacción.
- `dashboard.py` / `dashboard_ui.py`: snapshot BI con metadatos de `works`, etapas/coberturas/grupos/exportación y canvas adaptable. No confundir con `Store.dashboard`, que conserva los indicadores/validación legados para otros consumidores. Los filtros al escribir refrescan BI solo cuando está visible.
- `reporting.py`: 360 HTML, Kanban derivado, datasets y hechos. Usa inventario activo del ciclo vigente, nunca suma snapshots; tiempos con cobertura.
- `ui.py` + `operational_ui.py`: aplicación y flujo operativo. `coding_ui.py` + `coding_ui_v3.py`: visor/editor. `file_browser.py`: FlowBar y explorador virtual de miniaturas.
- `migrations.py`: núcleo 3 maestro/préstamo, 4 UUID/versiones/reconstrucción TIFF, 5 entregas/revisión, 6 correspondencia de adopción, 7 directorio/listas (`intake_schema.sql`, FK `lista_padre_id` para origen de legajos). Snapshot previo, transacción, rechazo de esquema futuro y columnas antiguas no reconocidas.
- `backup.py`/`manifests.py`: respaldo completo, rutas, referencias, restauración exclusiva. `asistente_actualizacion.py`: recorrido guiado que reutiliza el motor; `actualizar.py`/`update_recovery.py`: resguardo y sustitución solo de código, retorno bloqueado si datos cambiaron. `release.py`: lista cerrada del ZIP, incluye AGENTS.md.

Mapa y decisiones: [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md). Operación: [MANUAL_USUARIO.html](MANUAL_USUARIO.html). Instalación: [WINDOWS7.md](WINDOWS7.md). Las identidades antiguas ambiguas siguen pendientes de conciliación, sin sumar/borrar documentos. La app sigue siendo local de un operador; roles de servicios preparan reglas, no autenticación ni firma.

## Comandos y evidencia

```sh
.venv/bin/python main.py --workspace ensayos/listas-v06-final/demo
.venv/bin/python tools/run_tests.py --resultado .development/NOMBRE_NUEVO.json
.venv/bin/python tools/smoke_ui.py
.venv/bin/python tools/ensayo_oficina.py --destino ensayos/NOMBRE_NUEVO --ventanas
.venv/bin/python tools/build_release.py
```

Segundo perfil: `.venv-pillow95/bin/python`. El empaquetador produce `dist/Digitalizacion-0.6.2-codigo.zip`, manifiesto y `.sha256`. No añadir su propio hash dentro del ZIP: produciría una referencia circular. El fichero SHA-256 adyacente identifica exactamente la entrega. `.development/e2e_v061.py` ensaya desde 0.6.0; los anteriores `e2e_v06_from03.py`/`e2e_v06_from05.py` conservan evidencia de migraciones antiguas. Nunca abrir/modificar una base de oficina sin respaldo verificado y ensayo de copia.
