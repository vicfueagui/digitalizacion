# Digitalización 0.6.3 · kit de traslado conservador

Aplicación local Python/Tk/SQLite para recepción, digitalización TIFF, revisión y entrega de expedientes. Esta iteración prepara **Windows 7 → Windows 10** conservando el código operacional del origen, sus datos y el runtime3.8.10/Pillow9.5.0. El código capturado puede seguir siendo0.6.2; el kit se ejecuta desde otra carpeta. Sin cambios de esquema, interfaz operacional ni Docker obligatorio.

**Empieza aquí:** [Migración paso a paso](MIGRACION_WINDOWS10.html) · [Manual de uso](docs/MANUAL_USUARIO.html) · [Actualización de código, operación separada](ACTUALIZACION.html). Las guías son locales, imprimibles y funcionan sin internet.

## Qué entrega el kit

- **MIGRAR.bat**: auditar → exportar → comparar → restaurar → verificar → ensayar → habilitar. CLI equivalente: `migrar.py --help`.
- **AUDITAR_INTEGRIDAD.bat**, `diagnosticar_integridad.py`, `auditar_integridad_tiff.py`: SQLite, conteos, rutas, hashes, originales/revisiones/versiones y candidatos de recuperación con evidencia exacta.
- Manifiesto SHA-256 de cada documento y archivo de código, resumen de todas las tablas y prueba inversa de las normalizaciones aplicadas únicamente a la copia portable.
- Destino nuevo dividido en programa/workspace/herramientas, con barrera de restauración pendiente y **INICIAR_MIGRADO.bat** después de aceptación.
- Resolutor compartido que ejecuta y comprueba Python realmente; rechaza .venv vacía/inválida y permite alternativas compatibles. No depende de `python` en PATH.

## Trasladar a Windows 10

Obtén `dist/Digitalizacion-0.6.3-codigo.zip` y su `.sha256`. Verifica la huella y extrae el kit aparte. **No lo pegues encima de producción ni uses ACTUALIZAR para poder migrar.** Sigue [MIGRACION_WINDOWS10.html](MIGRACION_WINDOWS10.html).

El origen Windows7 se cierra, se exporta sin editar su base/TIFF y queda congelado como contingencia. Windows10 recibe un paquete verificado y restaura en una raíz nueva, que puede estar en otra unidad o usuario. Ensaya primero con el mismo código y runtime en datos ficticios. Habilita solo con controles correctos y confirmación del corte. No mantengas dos producciones.

La preparación se desarrolló con datos ficticios en Mac. **La migración real aún no está certificada**: falta ejecutar y conservar evidencia en ambos equipos, incluidos locking/BAT, teclado, TIFF reales y rendimiento con4GB. Consulta [resultados exactos](docs/VALIDACION_V063.md).

## Pruebas y Mac independiente

Los entornos de desarrollo están separados. El acceso `Digitalizacion-Pruebas-OSX-061.command` y sus sesiones existentes permanecen intactos. Consulta [LAPTOP.md](docs/LAPTOP.md) para ese laboratorio. Una demo nueva desde este código:

```sh
.venv/bin/python main.py --crear-demo /RUTA/NUEVA/demo
.venv/bin/python main.py --workspace /RUTA/NUEVA/demo
.venv/bin/python migrar.py
```

Para practicar el traslado, elige esa demo y marca **Solo laboratorio**. El paquete/destino debe estar fuera del código y del origen. `tools/ensayo_migracion.py --destino CARPETA_NUEVA_EXTERNA --codigo CODIGO_DE_ORIGEN` automatiza un ensayo completo exclusivamente ficticio; el intérprete debe tener Tk/Pillow/libtiff y una sesión gráfica.

```sh
.venv/bin/python tools/run_tests.py --resultado .development/RESULTADO_NUEVO.json
.venv/bin/python tools/smoke_ui.py
.venv/bin/python tools/smoke_migration_ui.py
.venv/bin/python tools/build_release.py
```

La suite incorpora regresiones de los incidentes reales. Python3.8.10 y3.13.15 se ejecutan en entornos locales independientes; no se presenta una comprobación de sintaxis como prueba de Windows. [Matriz y resultados](docs/VALIDACION_V063.md).

## Uso operacional que se conserva

CSV/XLSX por folio con columnas configurables, aceptación individual/múltiple sin recapturar CURP, directorios CRUD, legajos asociados, ciclo por préstamo, auditoría e indicadores con detalle. Codificación mantiene paneles ajustables, listas/detalles/miniaturas y Ctrl+rueda para tamaño; visor multipágina, edición con revisiones y originales inmutables. Entregas y versiones tienen manifiestos e historia independientes. El [manual con ejemplos](docs/MANUAL_USUARIO.html) explica casos y excepciones.

Workspace delimita SQLite, TIFF, versiones, entregas y reportes. Restaurar siempre requiere destino nuevo. El cierre automático respalda solo SQLite; para documentos utiliza **Respaldar base y TIFF**, verifica y conserva otra copia en medio autorizado. No reemplaces hashes para silenciar alertas ni sobrescribas originales.

## Documentación y próximos pasos

- [Diseño técnico de migración](docs/MIGRACION_TECNICA.md), [plan previo y diagnóstico del repositorio](docs/PLAN_MIGRACION_WINDOWS10.md).
- [Compatibilidad, deuda y hoja de ruta](docs/MODERNIZACION.md), [respaldo/restauración](docs/RESPALDOS.md), [Windows7](docs/WINDOWS7.md).
- [Contexto resumido](docs/CONTEXTO_PROYECTO.md), [bitácora acumulativa](docs/BITACORA_DESARROLLO.md), [arquitectura operacional](docs/MODELO_OPERATIVO_V05.md).

La siguiente fase evaluará Python moderno, empaquetado/CI, separación UI/servicios, configuración, OCR y procesamiento asíncrono en copias ficticias. Docker podrá servir para CI/servicios futuros; no es requisito en la HP de4GB. Los hashes TIFF cambian entre los Pillow ensayados, aunque coincidan sus píxeles: el candidato moderno no queda autorizado para reconstruir historia ni reemplazar producción.
