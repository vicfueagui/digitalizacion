# Validación de Digitalización 0.6.1

Fecha: 2026-09-23. Recepción por selección sin recaptura e Indicadores con resumen BI, barras adaptables y desglose. No cambia el esquema: núcleo 7 / TIFF 3. Solo pruebas locales con datos inventados; no se abrió producción.

| Comprobación ejecutada | Resultado y evidencia local |
|---|---|
| Suite CPython 3.11.4 / Pillow 12.3.0 | **218 ejecutadas, 210 aprobadas, 8 omitidas privadas, 0 fallos/errores**. `.development/v061-suite.json` |
| Suite CPython 3.11.4 / Pillow 9.5.0 | **218 ejecutadas, 210 aprobadas, 8 omitidas privadas, 0 fallos/errores**. `.development/v061-pillow95.json` |
| Recepción gráfica | Importar CSV, filtrar lista, seleccionar visibles, Cancelar sin cambio, confirmar cinco elementos con legajos conocidos y pendientes, crear ciclos sin recapturar CURP. `tools/smoke_ui.py` / `.development/v061-smoke-delivery.log` |
| Indicadores gráficos | 880×620, 1024×680, 1366×768; cifras dentro del canvas, color explícito, textos adaptados al ancho, porcentajes sin base al filtrar a cero, detalle y exportación. Redimensionar no consulta el servicio de datos; filtrar no reconstruye Kanban ni valida TIFF. Mismo smoke |
| Actualización 0.6.0 → 0.6.1 | SQLite byte a byte intacto al copiar código y abrir, sin migración. Se acepta una lista con legajo 2 existente y dos legajos pendientes confirmados como 1; BI filtrado y exportación, respaldo/restauración completos, TIFF previos intactos y retorno de código bloqueado tras cambiar datos. `.development/e2e-v061.log` / `e2e-v061-final.log` |
| Gramática Python 3.8 | 57 archivos Python distribuibles, analizados desde Python 3.11.4. `.development/gramatica-v061.json`. No constituye ejecución en Python 3.8.10 |

Se agregaron 18 pruebas: 11 en `tests/test_reception.py` y 7 en `tests/test_dashboard.py`. Incluyen confirmación explícita y legajo común, selección parcial, idempotencia, rollback por fallo tardío, discrepancias/extras, custodia en devolución, ciclo inactivo, permisos, otro folio, identidad existente, métricas filtradas y sin datos, conteo por legajo/CURP, retirada TIFF, ausencia de lectura de binarios, coberturas y exportación de filtros. Una primera prueba del panel omitía el conteo físico exigido antes de organizar; se corrigió el fixture, sin cambiar esa regla del programa.

Las ocho omisiones siguen siendo las pruebas de fuentes privadas originales ausentes. Las dos pruebas WAL reportadas para Windows y sus regresiones permanecen habilitadas y pasan en ambos perfiles locales. Se mantiene el smoke anterior de Codificación, miniaturas, Cancelar, 360, entregas, importación, legajos y directorio modal.

## Alcance y límites

El panel presenta estados y conteos registrados, no certifica integridad o vigencia de los binarios. Esas validaciones permanecen en los servicios de entrega/360. El cierre se muestra como estado registrado. Los elementos sin ciclo se muestran en un aviso global separado, no en el denominador de la vista filtrada. Los porcentajes de cobertura pueden superponerse; los de etapas usan una partición de los estados.

La aceptación rápida exige confirmar físicamente la selección. Usar legajo 1 es una propuesta visible que el operador puede cambiar antes de confirmar, no una inferencia del importador ni del consecutivo No. Las diferencias/faltantes/extras permanecen en revisión individual. La aceptación no asigna personal ni inventa el acuse del folio completo.

Windows 7 SP1 x64, CPython 3.8.10, bloqueos/junctions, teclado, escalado y rendimiento con TIFF grandes en 3 GB siguen pendientes de ejecución real. El perfil Pillow 9.5.0 se ejecutó en Mac con Python 3.11. La prueba de geometría/widgets no sustituye una revisión humana de comodidad visual.

## Entrega

`dist/Digitalizacion-0.6.1-codigo.zip`, manifiesto interno y `.sha256` adyacente; solo código, documentación, pruebas e instaladores permitidos. Los ZIP anteriores se conservan. Mac utiliza `codigo-0.6.1` independiente y el acceso `Digitalizacion-Pruebas-OSX-061.command`, con posibilidad de continuar las sesiones 0.6 existentes. No se sobrescribe su código anterior.

Guía: [RECEPCION_INDICADORES_V061.md](RECEPCION_INDICADORES_V061.md). Oficina: [WINDOWS7.md](WINDOWS7.md). Contexto: [CONTEXTO_PROYECTO.md](CONTEXTO_PROYECTO.md). Antecedentes: [VALIDACION_V06.md](VALIDACION_V06.md).
