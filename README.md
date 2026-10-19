# Digitalización web 0.8.2-dev

Respaldo de código y documentación solicitado el 2026-10-09 para el repositorio público vicfueagui/digitalizacion. Preparación retomada y cotejada el 2026-10-19. Rama prevista: respaldo/digitalizacion-web-0.8.2-hp-20261019. Conserva la etiqueta dev del paquete aprobado e instalado en la HP; no es una nueva versión del producto.

Esta instantánea contiene el código instalado, recursos locales con sus licencias, guías y pruebas sintéticas. **No contiene expedientes, TIFF, bases SQLite, cuentas, contraseñas de operación, reportes, respaldos ni intérpretes.** Tampoco configura sincronización continua. El historial de las ramas anteriores no se reescribe ni se certifica libre de datos por esta publicación.

## Estado y tecnologías

La instalación HP funciona desde INICIAR.bat con los datos originales y la cuenta existente, en http://127.0.0.1:8765. Núcleo 8 / TIFF 4. La instalación tuvo respaldo privado, copia restaurada y validada, migraciones y cotejo final. No copiar esta carpeta encima de una instalación: la activación verifica un manifiesto y la primera transición no actualiza una web ya activada.

Python web 3.14.8, Django 5.2.17 LTS, Pillow 12.3.0, Waitress 3.0.2 y WhiteNoise 6.12.0. Interfaz Django/HTMX 2.0.11, Bootstrap 5.3.8 y Chart.js 4.5.1, todos los recursos locales. Negocio compartido compatible con Python 3.8; el servidor web requiere el entorno moderno de requirements-modern.txt. No necesita Node ni CDN para trabajar.

## Funciones

Recepción y folios, expedientes por CURP/legajo, integraciones numeradas con conteo propio, cuatro vistas TIFF y estación de tres paneles, importación múltiple/carpeta, edición con revisiones, división/extracción/unión con procedencia por página, favoritos, códigos y lotes, indicadores y ayuda. Organizar / entregar produce otra entrega completa actualizada y conserva las anteriores. Hoja física, archivo TIFF, página y versión de entrega son unidades distintas.

Guías: [estación TIFF](docs/GUIA_ESTACION_TIFF_V082.md), [ergonomía e indicadores](docs/GUIA_WEB_V081.md), [operación web](docs/GUIA_WEB_V080.md). Sus instrucciones de apertura y etiquetas de candidata describen la preparación histórica congelada; las rutas de esa HP no existen en una descarga nueva. Las credenciales de ejemplo son exclusivamente ficticias.

## Evaluar en una copia separada

En otro directorio, usando un intérprete Python moderno compatible y un entorno propio, instalar los requisitos fijados y ejecutar tools/preparar_demo_web.py. Crea únicamente una nueva carpeta demo-web hermana del código; rechaza un destino que ya exista. Después ejecutar iniciar_web.py con --workspace apuntando a esa demo. No usar bases preexistentes ni las cuentas ficticias para operación. No se ejecutó una instalación nueva de dependencias para este respaldo.

INICIAR.bat de operación necesita python_web_ruta.txt y activación privada, excluidos deliberadamente. Descargar esta rama no restaura datos ni habilita una estación operativa por sí solo. Recuperar una oficina exige el resguardo privado, runtime compatible, revisión de capturas posteriores y procedimiento validado; no abrir TIFF 4 con código antiguo.

## Verificación y conservación

release-manifest.json identifica los 115 archivos originales del paquete instalado por SHA-256. Los demás archivos son soporte de desarrollo/documentación; la lista exacta de esta instantánea está en MANIFIESTO_RESPALDO.json. La documentación canónica pública es un resumen revisado, no una copia de bitácoras o informes privados de operación.

Las pruebas del producto y del respaldo se describen en [validación](docs/VALIDACION_WEB_V082_HP.md). La aceptación humana de la candidata fue comunicada antes de instalar; el rendimiento de una jornada completa y los atajos del teclado físico no se certifican mediante pruebas automáticas.

Para compartir contexto puede usarse EXPORTAR_CONTEXTO.bat con el entorno 3.8 indicado por ese acceso, o ejecutar tools/exportar_contexto.py con un intérprete disponible. El exportador requiere revisión explícita de documentos y sus huellas; no publica archivos ni conecta ChatGPT con la carpeta local.
