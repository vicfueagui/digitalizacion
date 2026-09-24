> Antecedente histórico. Para la entrega actual, consultar [VALIDACION_V05.md](VALIDACION_V05.md) y [MODELO_OPERATIVO_V05.md](MODELO_OPERATIVO_V05.md).

# Auditoría y decisiones de la entrega 0.4

## Diagnóstico de la copia recibida

La carpeta no contenía `.git` ni `AGENTS.md`; sí un bundle histórico. Se preservó una copia local del código recibido en `.development/original-code.zip`. No se importaron fuentes privadas. El README mezclaba v0.1–v0.3 y remitía a un LEEME.html inexistente. La suite constaba de 55 pruebas: en este Mac 47 pasaron y 8 dependían de fuentes privadas ausentes. No eran 55 aprobadas aquí.

Riesgos prioritarios encontrados y tratamiento:

| Riesgo | Hallazgo | Tratamiento |
|---|---|---|
| Mezclar producción/demo | `--db` cambiaba solo SQLite; TIFF, reportes y respaldos apuntaban al repositorio | Workspace único para todas las escrituras, demo exclusiva, arranque sin datos exige elegir raíz |
| Esquema | El visor reescribía `coding_schema_version` en cada inicio; executescript tenía commits implícitos | Migración central incremental y transaccional; versiones núcleo 2 / TIFF 3; snapshot previo y rechazo futuro |
| Identidad | Filtrar antes de agrupar elegía otro principal y ocultaba asociados | Agrupar primero; filtros estables; diagnóstico de relaciones; identidad fija; ninguna fusión |
| Archivos | Rutas Windows en Mac, symlinks, rename con reemplazo POSIX | Rutas portables validadas; rechazar escape; bloqueo por espacio; movimientos por enlace exclusivo y desvinculación |
| Correcciones | Una sustitución de página podía detenerse entre edición y retirada sin fase reanudable | Diario de sustituciones con fase confirmada en la misma transacción de cada cambio; Recuperar operación reanuda sin editar dos veces |
| Métricas | Cambio de carpeta del catálogo y fallo de reporte dejaban inventario anterior vigente | Invalidación explícita; publicación solo tras archivos/reporte/base coherentes; cero TIFF no permite cierre |
| Atajos | El catálogo no aceptaba HL-100 | Códigos hasta tres dígitos; configuración 1–999, secuencia al soltar Ctrl, protección de foco/modificadores |
| Visor | Rueda sin diferir render; giros finos sucesivos degradaban la previsualización | Debounce, conversión de modos solo para visualizar, composición de giros consecutivos, carga de una página |
| Actualización | Copiar una distribución completa podía incluir datos | ZIP con lista cerrada, manifiesto y hashes; actualizador respalda todo y solo copia código |

## Comportamiento deliberado y límites

- **No fusionar duplicados históricos**. Elegir un principal no combina TIFF, conteos, estados ni incidencias. `--duplicados` exporta las relaciones afectadas. Una fusión o una nueva interpretación de conteos requiere decisión del área y pruebas con copia autorizada.
- La normalización de CURP se aplica a altas/importaciones; no cambia masivamente CURP históricas. El folio puede cambiar con auditoría y conserva el ID del trabajo. Las fechas históricas no se inventan.
- **Organizar sigue requiriendo previsualización y confirmación**. Las acciones invalidan métricas y muestran que falta recalcular; no se mueven automáticamente documentos mientras se recorta o codifica. Después de terminar las correcciones, Organizar mide archivos activos/legibles y publica el reporte. Los reportes antiguos permanecen como evidencia sin sumarse. Es el organizador Python, no un BAT.
- Originales inmutables por las operaciones del programa; no se cambiaron permisos del disco. Una herramienta externa aún podría modificarlos: se detecta por hash y se bloquea la operación/respaldo. El bloqueo coordina instancias nuevas del programa, no herramientas externas ni versiones antiguas.
- Los movimientos requieren disco local que soporte enlaces duros (NTFS en Windows; APFS/HFS+ en Mac). Si no los admite, la operación falla conservando archivos. No se habilita una alternativa que pueda sobrescribir destinos. No usar datos activos en FAT/exFAT o red.
- Archivos incompletos tras un fallo de importación se conservan en recuperados. Un error de disco al revertir requiere conservar la carpeta y reintentar Recuperar operación; no se borran originales para “arreglar” el contador.
- Backups completos verifican todas las referencias TIFF. Si la copia antigua ya tiene archivos faltantes/alterados, el actualizador se detiene para no presentar un respaldo incompleto como utilizable. Los snapshots SQLite previos de migración no sustituyen un respaldo completo de oficina.
- No se hizo migración de producción ni se accedió al Lanix. Quedan pendientes el ensayo de Windows 7, teclado español físico, rendimiento en 3 GB, BAT, bloqueo Windows y enlaces NTFS. La sintaxis Python 3.8 por sí sola no prueba ese intérprete.
- El visor carga una página a la vez; limita 36 Mpx por página y 16 Mpx de vista. No hay caché de expedientes completos. Las operaciones TIFF y respaldos siguen siendo síncronas; en documentos grandes la interfaz puede esperar. Se conserva cursor de progreso y errores recuperables. Pasar cálculo pesado a un trabajador es mejora posterior, con SQLite y Tk confinados a sus hilos respectivos.
- No se verificó manualmente cada combinación Retina/trackpad/teclado. Las pruebas gráficas abren ventanas reales y ejercitan cancelación/paneles/zoom; las pruebas automáticas no determinan comodidad o nitidez subjetiva.
- Paquetes con SHA-256 detectan alteraciones; no equivalen a firma digital ni sustituyen una fuente de distribución autorizada. No hay autenticación institucional ni cifrado de expedientes.

## Trabajo posterior, por prioridad

1. Validar Windows 7 con la demo y un respaldo restaurado localmente, registrar memoria/tiempos y autorizar el momento del primer arranque en producción. No usar esta validación para prometer soporte vigente del SO.
2. Revisar en el área cualquier duplicado histórico y referencias de ubicación física de reescaneos. Definir una eventual fusión por expediente con conciliación explícita; no sumar por intuición.
3. Evaluar hardware/OS soportado y el intérprete mantenido del Mac. Después, mover trabajo pesado fuera del hilo UI y automatizar el ensayo de Python 3.8/Windows en un equipo autorizado. Docker solo en una plataforma soportada y para pruebas acotadas.
