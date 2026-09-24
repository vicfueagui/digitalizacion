> Antecedente histórico. Para la entrega actual, consultar [VALIDACION_V05.md](VALIDACION_V05.md) y [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md).

# Cambios y validación 0.4.1 — 21 de septiembre de 2026

Actualización implementada y probada en la copia de desarrollo del Mac, exclusivamente con información ficticia. **La instalación y los datos de Windows 7 no se abrieron ni actualizaron.** Esta entrega sustituye al paquete 0.4 para el próximo ensayo. Conserva las versiones de esquema núcleo 2 / TIFF 3.

## Defectos corregidos

| Cambio | Resultado |
|---|---|
| Fallo al desvincular el origen de un movimiento TIFF | Retira únicamente el enlace recién creado; si también falla esa limpieza, conserva la operación pendiente para Recuperar y bloquea nuevas acciones incompatibles |
| Manifiestos de respaldo y actualización | Rechaza rutas no portables, nombres reservados, hashes inválidos, colisiones, enlaces y junctions; detecta documentos referenciados que faltan en la lista antes de crear el destino de restauración |
| Cambio de folio o conteo físico confirmado | Invalida reportes anteriores y exige regenerar el inventario; un CSV externo no puede reemplazar las métricas de TIFF gestionados |
| Recuperación de código | Comprueba esquema/filas SQLite —incluido WAL—, documentos y reportes; rechaza el retorno tras migraciones, capturas o cambios posteriores. Restituye únicamente código reconocido y admite reintento tras interrupción |
| Ensayo de oficina | Automatiza pruebas, demo, respaldo, verificación, restauración y ventanas opcionales; registra resultados locales y deja explícita la revisión humana pendiente |
| Fuentes privadas | Ocho pruebas históricas requieren habilitación explícita; el ensayo sintético siempre las desactiva |

Archivos principales: `app/manifests.py`, `app/update_recovery.py`, `app/backup.py`, `app/coding.py`, `app/coding_v3.py`, `app/core.py`, `actualizar.py`, `tests/test_continuation.py`, `tools/run_tests.py` y `tools/ensayo_oficina.py`. La versión mostrada y el paquete usan `app.VERSION`.

## Resultados locales

| Comprobación | Resultado |
|---|---|
| Mac Intel / Big Sur / Python 3.11.4 / Pillow 12.3.0 | **122 pruebas: 114 aprobadas, 0 fallidas, 0 errores, 8 omitidas** |
| Mismo Mac / Python 3.11.4 / Pillow 9.5.0 en entorno separado | **122 pruebas: 114 aprobadas, 0 fallidas, 0 errores, 8 omitidas** |
| Nuevas regresiones 0.4.1 | 21 pruebas sintéticas de movimientos, métricas, manifiestos y recuperación |
| Gramática compatible con Python 3.8 | 31 archivos Python verificados; no es ejecución con ese intérprete |
| Ensayo automatizado | Demo, diagnóstico, respaldo, verificación, restauración y base intacta al respaldar: correctos |
| Ventanas reales en este Mac | App y visor TIFF abiertos; ImageTk, zoom, paneles y Cancelar conservando edición: correctos |
| ZIP sobre el código original 0.3, con datos ficticios | Comprobación y actualización correctas; SQLite idéntico durante la copia; recuperación del código anterior sin alterar base/TIFF; segunda actualización y migración conservan IDs, dos legajos, conteo y originales. Tras migrar/organizar, el retorno se rechaza sin modificar datos ni código |
| Windows 7 SP1 / Python 3.8.10 / BAT / NTFS | **Pendiente de ejecución en el equipo de oficina** |

Las ocho omitidas dependen de fuentes privadas y se complementan con pruebas de importación sintéticas. Las pruebas Windows de enlaces pueden tener omisiones adicionales, identificadas individualmente. Los resultados no certifican archivos privados, el teclado físico de oficina ni rendimiento de TIFF grandes en 3 GB de RAM.

Evidencia local, excluida del ZIP: `ensayos/mac-v041-final/resultado.json`, sus registros, `.development/results-pillow95-v041-final.json` y `.development/e2e-release-v041.txt`. El informe mantiene `produccion_validada: false` y `perfil_windows7_coincide: false` porque este equipo es un Mac. El ensayo integral usó carpetas temporales con espacios y referencias TIFF con separadores de Windows; tampoco representa ejecución en Windows.

## Entrega

`dist/Digitalizacion-0.4.1-codigo.zip` y su `.sha256` transportan exclusivamente código, pruebas, documentación e instalador Pillow legado. No contienen expedientes, bases SQLite, TIFF de trabajo, entornos virtuales ni resultados locales. El ZIP incluye un manifiesto de hashes que el actualizador comprueba antes de copiar código.

Para regenerarlo desde Terminal en esta laptop:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python tools/build_release.py
```

El paquete previo 0.4 y `.development/original-code.zip` se conservan como antecedentes. No hubo cambios de sistema, publicación ni traslado de datos originales.

## Siguientes pasos en oficina

1. Trasladar el ZIP 0.4.1 y su SHA-256, comprobarlos y extraer fuera de producción siguiendo [WINDOWS7.md](WINDOWS7.md).
2. Preparar la `.venv` local y completar el [ensayo sintético](ENSAYO_OFICINA.md), además de las comprobaciones humanas de visor/teclado/rendimiento.
3. Con la aplicación cerrada, comprobar/aplicar la actualización, conservar el resguardo y comparar los datos en el primer arranque antes de retomar captura. Ante discrepancias, conservar los estados y revisar; no restaurar encima de captura posterior.

Los límites y decisiones de la entrega 0.4 siguen documentados en [AUDITORIA_V04.md](AUDITORIA_V04.md), y el soporte de plataformas en [COMPATIBILIDAD.md](COMPATIBILIDAD.md).
