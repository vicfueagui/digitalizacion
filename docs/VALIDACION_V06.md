# Validación de Digitalización 0.6.0

Antecedente de la entrega anterior. Versión actual: [VALIDACION_V061.md](VALIDACION_V061.md).

Fecha: 2026-09-22. Ampliación de listas CSV/XLSX por folio, varios legajos por CURP, directorio operativo y filtros inmediatos. Solo datos ficticios; no se abrió producción. El [informe 0.5.0](VALIDACION_V05.md) conserva los antecedentes del modelo, corrección WAL y Codificación.

## Comprobaciones ejecutadas

| Comprobación | Resultado / evidencia local |
|---|---|
| Suite, CPython 3.11.4 + Pillow 12.3.0 | **200 ejecutadas: 192 aprobadas, 8 omitidas privadas, 0 fallos/errores**. `.development/v060-suite.json` |
| Suite, CPython 3.11.4 + Pillow 9.5.0 | **200 ejecutadas: 192 aprobadas, 8 omitidas privadas, 0 fallos/errores**. `.development/v060-pillow95.json` |
| Interfaz Tk real | Importación con vista previa y opciones, tres legajos, edición de directorio dentro de formulario modal y retorno del foco, búsqueda con pausa sin reconstruir Kanban, columnas TIFF/páginas. También visor 860/1024/1366, miniaturas virtuales y cancelación. `.development/v060-smoke.log` |
| Gramática Python 3.8 | 51 archivos Python distribuibles, AST desde Python 3.11.4. `.development/gramatica-v06.json`. No equivale a ejecutar CPython 3.8.10 |
| Actualización desde 0.5.0 / núcleo 6 | ZIP previo + demo ficticia → código nuevo sin cambiar SQLite → núcleo 7; todas las filas y columnas anteriores conservadas, TIFF intactos, nombres enlazados al directorio. Lista + tres legajos sobreviven a respaldo/restauración; recuperación de código rechazada después de cambiar datos. `.development/e2e-v06-from05.log` |
| Actualización desde 0.3 | Sustitución de código sin modificar SQLite → recuperación del código anterior → reaplicación → migración preservando IDs, conteos, legajos, TIFF multipágina y entrega verificable; retorno posterior rechazado. `.development/e2e-v06-from03.log` |
| Ensayo completo | Demo, diagnóstico, suite, respaldo, verificación, restauración, diagnóstico restaurado y ventanas. `ensayos/listas-v06-final/resultado.json` |

Las ocho omisiones son pruebas históricas con Excel/CSV privados ausentes. No se activaron ni se contaron como aprobadas. Las dos pruebas WAL reportadas para Windows continúan habilitadas y pasan localmente; también sus regresiones sobre exclusión antes de resolver rutas y rechazo de archivos incluidos inaccesibles.

## Regresiones nuevas

`tests/test_intake.py` añade 17 pruebas: encabezados como los solicitados con identidades ficticias, CSV reordenado/Windows-1252, UTF-16/tabulación, XLSX con encabezado desplazado y fecha numérica, correspondencia manual, folio por defecto, No. separado de legajo, campos ausentes, RFC/identidad discordante/fecha inválida, fuente modificada, rollback completo de lote, idempotencia sin sobrescribir recepción/asignación, segundo folio del mismo maestro, varios legajos con inventarios separados y procedencia compartida, confirmación individual, fallo de desglose, búsqueda parcial sin leer TIFF y CRUD con referencias/alias/baja/reactivación.

`tests/test_model_migration.py` añade dos pruebas: referencias del directorio sin cambiar IDs ni nombres/fechas históricos y rollback completo si falla la población inicial del directorio. Se mantienen las cinco regresiones anteriores de migración.

No se usaron nombres o documentos reales para fixtures, demos ni esta documentación. El generador crea un CSV de práctica sin importarlo automáticamente, por lo que la demo sigue mostrando sus tres expedientes iniciales hasta que el usuario hace el ejercicio.

## Entrega y límites

`dist/Digitalizacion-0.6.0-codigo.zip` contiene solo archivos permitidos de código, documentación, pruebas e instalación, además del manifiesto. Su SHA-256 está en el archivo adyacente `.sha256`; los ZIP 0.5.0 y 0.4.1 se conservan. La copia independiente de Mac usa otra carpeta de código y otras sesiones, sin migrar las pruebas anteriores.

**Pendiente de ejecución real:** Windows 7 SP1 x64 / CPython 3.8.10 / Pillow 9.5.0, bloqueos y junctions reales, teclado, escala/ergonomía y rendimiento con los volúmenes de oficina en 3 GB. También debe cotejarse una copia autorizada de los datos originales. El perfil Pillow 9.5.0 ejecutado aquí sigue siendo macOS/Python 3.11.

No se soporta `.xls` binario ni se transforma un RFC en CURP. Los nombres desconocidos/ambiguos requieren correspondencia manual; la importación no interpreta cualquier estructura libre de Excel. Los archivos con calendario 1904 deben convertirse antes. Las filas con errores se conservan para revisión. El archivo y configuración idénticos no se reprocesan; la recepción física y las discrepancias requieren confirmación operativa. La experiencia gráfica automatizada no sustituye una revisión humana en la pantalla de oficina.

Flujo: [IMPORTACION_FOLIOS_V06.md](IMPORTACION_FOLIOS_V06.md). Actualización: [WINDOWS7.md](WINDOWS7.md). Continuidad: [CONTEXTO_PROYECTO.md](CONTEXTO_PROYECTO.md) y [BITACORA_DESARROLLO.md](BITACORA_DESARROLLO.md).
