# Compatibilidad y modernización posterior

Fecha de revisión: 2026-09-23. El kit 0.6.3 prepara la migración. Ningún candidato moderno queda autorizado para producción. Primero debe existir aceptación Windows 7 → Windows 10 del código actual, sin cambios de dominio/esquema.

## Matriz inicial reproducible

| Perfil | Python / Pillow | Uso | Evidencia |
| --- | --- | --- | --- |
| Producción conservadora | CPython3.8.10 x64 / 9.5.0 | Primera migración; Tk8.6/libtiff, mismas SQLite/Tcl del origen | Suite ejecutada también en Mac con3.8.10; aceptación Windows7/10 pendiente |
| Puente de desarrollo existente | CPython3.11.4 / 9.5.0 | Aislar cambio Python conservando Pillow | Entorno local independiente |
| Desarrollo Mac existente | CPython3.11.4 / 12.3.0 | Laboratorio actual de UI | No instalar en el Win7 productivo |
| Candidato moderno | CPython3.13.15 x64 / 12.3.0 | Laboratorio separado con Tk8.6; build estándar con GIL | Suite local; falta matriz Windows y corpus representativo |
| Observación futura | Serie3.14 | Evaluar después de3.13 | Sin perfil productivo ni prueba certificada en esta entrega |

Las cifras exactas, versiones SQLite/Tk/libtiff y omisiones están en [VALIDACION_V063.md](VALIDACION_V063.md). Ejecutar gramática compatible3.8 no sustituye correr CPython3.8.10; esta entrega prepara y ejecuta un entorno real de esa versión en Mac, con bibliotecas distintas del binario oficial Windows.

Python3.13.15 es una versión estable publicada el5 de agosto de2026; se elige como candidato maduro para laboratorio, sin obligar a usar la serie más nueva. [Release oficial](https://www.python.org/downloads/release/python-31315/). Pillow9.5 soporta Python hasta3.11; Pillow12 incluye3.13, por lo que no se promete probar Pillow9.5 en3.13 como perfil soportado. [Matriz oficial Pillow](https://pillow.readthedocs.io/en/stable/installation/python-support.html).

## Dependencias e instalación

`requirements-legacy.txt` y `requirements.txt`: Pillow==9.5.0. `requirements-laptop.txt`: Pillow==12.3.0, perfil Mac previo. `requirements-modern-lab.txt`: Pillow==12.3.0, candidato3.13.15. Son perfiles distintos; no se combinan. La aplicación solo depende funcionalmente de Pillow además de stdlib/Tk/SQLite.

El wheel cp38-win_amd64 de Pillow9.5 está en instaladores, con SHA-256 y licencia; el instalador lo comprueba antes de pip --no-index --no-deps. No descarga versiones ambiguas. El intérprete y sus bibliotecas se inventarían durante cada ensayo. Los wheels de laboratorio dependen de la plataforma; conservarlos y registrar hashes al cerrar la siguiente release moderna. No se incluye un falso lock universal entre Windows y Mac.

Ejemplo para el siguiente laboratorio Windows, una vez certificada la migración: instalar CPython3.13.15 x64 en ubicación nueva, crear otro venv, instalar `--only-binary=:all: -r requirements-modern-lab.txt`, correr `tools/run_tests.py --resultado RESULTADO_NUEVO.json`, prueba gráfica y corpus TIFF. No modificar python_ruta.txt de producción. La detección conservadora de los BAT seguirá rechazando el moderno para primera migración.

## Puertas de aceptación antes de modernizar

1. Certificar origen/destino real con runtime legado, abrir datos y TIFF y conservar evidencias/rollback.
2. Repetir suite y gráficos en Windows10 con ambos runtimes, cada uno en demo separada; cubrir encoding, rutas, timestamps, subprocess, SQLite, locks y publicaciones.
3. Ejecutar corpus TIFF conocido: B/N, gris, RGB, multipágina, giros rectos/finos, recortes, reemplazos, metadata, compresión y tamaños representativos. Medir RAM y duración con4GB.
4. Comparar píxeles/páginas/metadata y SHA de bytes POR SEPARADO. `tools/tiff_compat.py` permite crear una referencia sintética con el legado y comparar desde el candidato. No cambia los hashes registrados; una diferencia de bytes impide declarar equivalencia de reconstrucción histórica.
5. Mantener un runtime legado de recuperación mientras existan cadenas TIFF que dependan de su codificador. No recalcular masivamente hashes históricos.
6. Proponer una release moderna independiente con manifiesto, pruebas, instaladores y rollback. Eliminar compatibilidad3.8 solo tras aceptación explícita y documentación de recuperación.

Python3.8 terminó su soporte; se conserva temporalmente para reducir variables del traslado. [Información oficial3.8.10](https://www.python.org/downloads/release/python-3810/). Separar las fases evita convertir ese compromiso temporal en arquitectura permanente.

## Deuda técnica y prioridades

| Prioridad | Hallazgo | Siguiente cambio acotado | Condición |
| --- | --- | --- | --- |
| P0 | Faltan evidencias de las dos máquinas reales | Ejecutar traslado/doble ensayo/corte y rollback previo a captura | Antes de certificar migración |
| P1 | Código de oficina puede divergir del local pese a misma versión | Conservar manifiesto capturado y reconciliar diferencias en otra revisión | No sustituir código durante traslado |
| P1 | Runtime3.8 y Windows10 general fuera de soporte | Perfil moderno validado y revisión de cobertura ESU/LTSC | Decisión separada de TI |
| P1 | Persistencia/servicios grandes y mixins acoplados a Store | Interfaces de repositorio/unidad de trabajo; extraer un caso por vez | Mismas transacciones/auditoría/tests |
| P1 | Algunas historias contienen rutas absolutas libres | Nuevos eventos con identificadores relativos tipados | Conservar eventos previos como evidencia |
| P1 | Respaldo, diagnóstico y hash recorren archivos varias veces | Cache de verificación por operación y snapshot estable | No reducir comprobación de mutaciones |
| P2 | Operaciones largas Tk parcialmente síncronas | Trabajador de I/O con progreso/cancelación segura | Nunca cancelar entre cambio físico y diario sin recovery |
| P2 | Configuración en meta, archivos locales y argumentos | Modelo versionado de configuración explícita | No meter nombres de usuario en referencias |
| P2 | Comparación all-table ordena un hash por fila en RAM | Ordenación externa por lotes si crece el volumen | Medir primero en4GB |
| P2 | No CI Windows7/Windows10 demostrado | Runners controlados; matriz de runtimes y corpus | No usar fuentes productivas en CI |
| P2 | Logs heterogéneos y estado local sin firma | Eventos estructurados con IDs, redacción y retención | No enviar CURP/TIFF a telemetría |
| P3 | Distribución de código/venv manual | Evaluar empaquetado nativo reproducible | Conservar manifiesto y runtime recuperable |
| P3 | OCR/clasificación inexistentes | Servicio opcional con resultados derivados/versionados | No modificar originales, hashes ni aceptar sugerencias sin revisión |
| P3 | SQLite local de un operador | Medir necesidad antes de evaluar servidor DB | Nueva fase de concurrencia, permisos y respaldo |

## Docker y hardware

La HP de4GB ejecutará Python/Tk nativo. Docker Desktop no es requisito y no se instala. Un contenedor puede ser útil después para CI de servicios sin UI, conversiones ficticias u OCR aislado en una máquina con recursos; no comprueba Tk ni bloqueo NTFS/Windows. No se añade un Dockerfile que aparente certificar el escritorio mediante pruebas Linux.

OCR, clasificación documental y colas asíncronas consumen RAM y requieren límites de página/lote, disco temporal controlado y mediciones. Evitar cargar expedientes enteros en memoria. La aplicación ya procesa TIFF y miniaturas con límites; conservarlos en cualquier rediseño.

## Compatibilidad de actualizaciones futuras del destino dividido

El lanzador migrado sella programa y herramientas mediante su manifiesto inicial. Cambiar esos archivos bloquea el arranque hasta un nuevo procedimiento validado. El actualizador histórico está diseñado para código y datos en una raíz; no se aplica directamente a `programa/` aislado, ni se retoca migracion.json para omitir diferencias. Antes de una futura release, preparar un actualizador que entienda el destino dividido y archive la aceptación anterior. Eso se mantiene como deuda explícita, fuera del traslado inicial.

## Hallazgos concretos del candidato de esta iteración

El corpus de cuatro TIFF produjo píxeles/páginas/metadata comparada iguales, pero los cuatro SHA de bytes difieren entre Pillow9.5/libtiff4.5 y Pillow12.3/libtiff4.7.1. Además, la prueba gráfica con3.13.15 completó controles pero emitió un error de finalización de AppendingTiffWriter (`seek of closed file`). Ambos hallazgos quedan como barreras para la siguiente fase; no se silencian ni se alteran hashes para aprobarla. La suite funcional por sí sola no demuestra equivalencia de reconstrucción histórica.
