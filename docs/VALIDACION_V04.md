> Antecedente histórico. Para la entrega actual, consultar [VALIDACION_V05.md](VALIDACION_V05.md) y [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md).

# Entrega y validación 0.4 — 21 de septiembre de 2026

Registro histórico de la entrega 0.4. La entrega vigente y sus resultados se describen en [VALIDACION_V041.md](VALIDACION_V041.md); el constructor actual genera el paquete 0.4.1.

## Resultado comprobado

Se implementó la actualización en la copia de desarrollo del Mac, con datos inventados. **No se modificó la instalación ni la información original de Windows 7.** El paquete de código y el procedimiento protegido quedan listos para el ensayo de oficina; la compatibilidad real del Lanix sigue pendiente.

| Comprobación | Resultado |
|---|---|
| Código recibido, Python 3.11.4 / Pillow 12.3.0 / Mac | 55 pruebas ejecutadas: **47 aprobadas, 0 fallidas, 8 omitidas**; 51.527 s |
| Código actualizado, Python 3.11.4 / Pillow 12.3.0 / Mac | 101 pruebas ejecutadas: **93 aprobadas, 0 fallidas, 8 omitidas**; 59.264 s |
| Código actualizado, Python 3.11.4 / Pillow 9.5.0 / Mac, entorno separado | 101 pruebas ejecutadas: **93 aprobadas, 0 fallidas, 8 omitidas**; 55.758 s |
| Gramática Python 3.8 | 26 archivos Python correctos; no es ejecución del intérprete 3.8 |
| Dependencias de desarrollo | `pip check`: sin dependencias incompatibles |
| Wheel legado incluido | SHA-256 coincide con `instaladores/SHA256.txt`; no se ejecutó el wheel Windows en Mac |
| Tk local | Ventana abierta con Tcl/Tk 8.6.12; resolución lógica informada 1440×900 |
| App y visor local | Prueba gráfica automática abrió ventanas e imágenes; zoom, paneles, ImageTk y Cancelar conservando edición pasaron |
| Demo y CLI | Demo creada; diagnóstico sin alterar base; respaldo completo verificado; restauración en destino nuevo correcta |
| Actualización integral de v0.3 a v0.4, solo en Mac | Se extrajo el código recibido en una carpeta temporal con espacios, se generaron dos legajos/conteo/TIFF ficticios y rutas con separadores Windows. Se aplicó el ZIP: SQLite quedó idéntico durante la copia; el primer arranque migró y conservó IDs, legajos, conteo y TIFF; organización posterior correcta |
| Windows 7 / Python 3.8.10 / BAT / NTFS | **No ejecutado en este equipo**; usar el ensayo de WINDOWS7.md |

Las ocho omitidas son `SourceTests` de `tests/test_domain.py`: necesitan el Excel y CSV privados que no forman parte de esta copia. `test_synthetic_sources.py` complementa importaciones, normalización, dos legajos, duplicados, relaciones, CSV idempotente, inventario parcial y filas rechazadas con fuentes inventadas; no certifica un archivo real no disponible.

Los tiempos son del Mac y de imágenes pequeñas de ensayo. No predicen el rendimiento con TIFF reales en 3 GB RAM. Los logs completos locales están en `.development/baseline-tests.txt`, `.development/tests-v04.txt` , `.development/tests-pillow95.txt` y `.development/e2e-release.txt`; se excluyen del paquete distribuible.

## Cambios y archivos

| Archivos | Qué resuelven |
|---|---|
| `main.py`, `app/workspace.py`, `app/demo.py` | Raíz coherente, aislamiento, diagnóstico sin escrituras, demo nueva sin sobrescribir destino, CLI de respaldo/restauración |
| `app/migrations.py`, `app/migration_sql.py`, `app/core.py` | Versiones incrementales, transacciones, snapshot previo, rechazo futuro, principal estable, diagnóstico de duplicados y catálogo de tres dígitos |
| `app/backup.py` | SQLite backup API, exportación portable de rutas conocidas en la copia, verificación de documentos y restauración exclusivamente nueva |
| `app/coding.py`, `app/coding_v3.py` | Rutas seguras, exclusión de procesos, movimientos sin reemplazo, diario de operaciones/sustituciones, preservación de páginas y métricas desactualizadas |
| `app/coding_ui.py`, `app/coding_ui_v3.py`, `app/ui.py` | Paneles y tamaños persistentes, texto completo, zoom diferido, foco de teclado, vista previa de reemplazo, exportación física de reescaneos |
| `app/importers.py` | Identidad normalizada al buscar coincidencias y aceptación de códigos de tres dígitos sin borrar origen |
| `tests/test_safety.py`, `test_keyboard.py`, `test_synthetic_sources.py`, `test_update.py` | 46 regresiones nuevas: aislamiento, migración/fallos, WAL, rutas, interrupciones, reemplazo reanudable, actualización y fixtures sintéticos |
| `tools/smoke_ui.py` | Ensayo gráfico automático con datos temporales, sin expedientes reales |
| `actualizar.py`, `app/release.py`, `tools/build_release.py` | Lista cerrada de código, manifiesto, respaldo previo, comprobación de destino y recuperación de copia fallida |
| `instalar_visor.py`, perfiles de requisitos, BAT, `iniciar.sh` | Instalación local en .venv por plataforma, wheel legado verificado y comandos con rutas entre comillas |
| `.gitignore`, `.dockerignore`, `README.md`, `ACTUALIZACION.html`, guías v0.4 | Excluir información operativa y distinguir documentación vigente de histórica |

Se conservaron `app/schema.sql`, las pruebas originales, el wheel legado y `repositorio_v03.bundle`. La copia del código recibido está en `.development/original-code.zip`. No se hizo push, publicación, instalación del sistema, cambio de SO ni migración de datos reales.

## Comandos de la laptop

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python main.py --workspace demos/demo-v04
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python tools/smoke_ui.py
```

Para otra demo, usa un destino que no exista:

```sh
.venv/bin/python main.py --crear-demo demos/ensayo-nuevo
.venv/bin/python main.py --workspace demos/ensayo-nuevo
```

La comprobación adicional de API de Pillow 9.5.0 se hizo en `.venv-pillow95`, sobre el Python 3.11.4 del Mac. No copies ese entorno a Windows ni lo confundas con la prueba pendiente de Python 3.8.10. Si deseas repetirla en este mismo Mac:

```sh
.venv-pillow95/bin/python -m unittest discover -s tests -v
```

Para regenerar el paquete solo de código:

```sh
.venv/bin/python tools/build_release.py
```

Genera `dist/Digitalizacion-0.4-codigo.zip` y `dist/Digitalizacion-0.4-codigo.sha256`. El manifiesto interno se verifica antes de actualizar y no autoriza rutas de datos. SHA-256 confirma integridad del traslado, no identidad del emisor.

## Tres siguientes pasos para el operador

1. **Abrir la demo del Mac** con el comando anterior. Reconocerás el éxito por el título DEMOSTRACIÓN FICTICIA, tres expedientes y dos legajos de una misma identidad; abre Codificar para ver las páginas.
2. **Llevar únicamente el ZIP y su SHA-256 a Windows 7**, extraer fuera de producción y seguir [WINDOWS7.md](WINDOWS7.md), pasos 1 y 2. Deben abrirse la ventana Tk y la demo con Python 3.8.10/Pillow 9.5.0, sin fallos en las pruebas disponibles.
3. **Con la aplicación de oficina cerrada, comprobar y aplicar la actualización** conforme a los pasos 3 y 4 de esa guía. Debe aparecer un resguardo verificado y conservarse los IDs, conteos, TIFF e historial al abrir el proyecto. Si algo no coincide, detener la captura y conservar ambos estados para revisión.

Docker no se usa ni se recomienda en Big Sur; la razón y fuentes oficiales están en [COMPATIBILIDAD.md](COMPATIBILIDAD.md). Las decisiones de fusión de duplicados, migración de SO y validación física pendiente están explícitas en [AUDITORIA_V04.md](AUDITORIA_V04.md).
