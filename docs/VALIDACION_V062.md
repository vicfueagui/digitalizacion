# Validación de la entrega 0.6.2

Alcance: documentación integral, guía de actualización para principiantes, asistente Tk que reutiliza `actualizar.py` y botón Ayuda. Núcleo 7 / TIFF 3 sin cambios. No se accedió a producción ni se ejecutó Windows 7 en esta sesión.

## Pruebas ejecutadas en Mac

- CPython 3.11.4 con Pillow 12.3.0 y 9.5.0: **231 ejecutadas, 223 aprobadas, 8 omitidas privadas, 0 fallos, 0 errores**. Evidencia local: `.development/v062-suite.json` y `v062-pillow95.json`. Las omisiones no se cuentan como aprobadas.
- 13 regresiones nuevas del asistente: selección y comprobación de lectura, aislamiento de ensayos, cambio de destino/manifiesto, archivo alterado, confirmación obligatoria, informe fallido/de otra versión, perfil Windows exigido, entorno ausente, invocación del motor sin shell y conservación de registros ante fallo. Los perfiles Windows de estas pruebas se simulan; no representan ejecución en ese sistema.
- Se mantienen habilitadas las pruebas `test_wal_committed_data_also_blocks_recovery` y `test_backup_wal_and_corruption_refused`, así como las regresiones de exclusión previa a resolver SHM y de error de permiso sobre archivos incluidos. Pasan localmente; no se modificó el motor de respaldos.
- Tk real: ventana del asistente en 700/820/1024 píxeles, controles dentro de la ventana, bloqueo durante el trabajo, respuesta mediante cola y cierre protegido (`v062-smoke-asistente.log`). Visor, miniaturas, recepción, directorio, Indicadores y enlace Ayuda en `v062-smoke-ui.log`.

- E2E con código archivado 0.6.1 y demo ficticia: el asistente ejecuta su ensayo real y aplica 0.6.2; conserva SQLite byte por byte, todos los TIFF y referencias, abre sin migración, verifica/restaura el respaldo y permite retorno del código anterior antes de nuevas capturas. Evidencia del candidato: `.development/e2e-v062-candidato-corregido.log`. El fallo inicial del script de ensayo fue una llamada con argumentos invertidos al retorno; se corrigió el harness, no el motor.
- Gramática Python 3.8 verificada en **61 archivos**. Enlaces locales y anclas de ambos HTML comprobados (`v062-documentos-gramatica.json`). Guía renderizada e inspeccionada mediante Chrome local; navegador e impresión Windows pendientes.

No hay datos personales en estas pruebas. Los resultados corresponden al código del paquete; la bitácora registra el cierre de distribución.

## Pendientes en el equipo de oficina

Ejecutar el paquete entregado en **Windows 7 SP1 x64, CPython 3.8.10 x64, Tk y Pillow 9.5.0**. Seguir [la guía](../ACTUALIZACION.html) y conservar el resultado del ensayo de ese equipo. Revisar doble clic del BAT, rutas con espacios/acentos, fuentes/escalado, navegador e impresión del manual, rueda y teclado físicos, bloqueos/junctions y rendimiento con TIFF representativos en 3 GB.

Ensayar primero con datos ficticios y, cuando corresponda por migración o dudas históricas, con una copia real autorizada restaurada en carpeta nueva. El asistente exige el perfil previsto en Windows pero el éxito automático no certifica la información productiva ni sustituye esa comparación humana. La compatibilidad sintáctica de Python 3.8 tampoco equivale a ejecutarlo.

## Distribución

`Digitalizacion-0.6.2-codigo.zip`, manifiesto interno de hashes por archivo y SHA-256 adyacente del ZIP. Solo archivos permitidos de código, pruebas, documentación e instalación; sin SQLite, TIFF, demos, reportes operativos, `.venv` ni sesiones del laboratorio Mac. No se incrusta la huella final del ZIP dentro de sí mismo para evitar una referencia circular.
