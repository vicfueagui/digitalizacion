# Ensayo reproducible con datos ficticios

Esta herramienta comprueba el código en el equipo donde se ejecuta. Crea una carpeta nueva y no abre la instalación productiva. No necesita Excel, CSV ni TIFF personales. No instala componentes ni usa la red.

## En Windows 7

Prepara el paquete y su entorno según [WINDOWS7.md](WINDOWS7.md), paso 1. En **cmd.exe**, desde el paquete extraído:

```bat
cd /d "C:\ActualizacionDigitalizacion062"
.venv\Scripts\python.exe tools\ensayo_oficina.py --destino "C:\PruebasDigitalizacion\ensayo062" --ventanas
```

Elige una carpeta que no exista. No uses la carpeta de producción. Las ventanas de comprobación se abren y se cierran solas; déjalas terminar. La consola muestra cada etapa y la ruta del informe. Si vuelves a probar, usa otro nombre de destino. Sin `--ventanas` no se comprueba la interfaz gráfica.

El informe `resultado.json` incluye:

| Campo | Interpretación |
|---|---|
| `entorno` | Sistema, Service Pack, implementación/versión/arquitectura de Python, SQLite, Pillow y libtiff detectados |
| `perfil_windows7_coincide` | Verifica Windows 7 SP1, CPython 3.8.10 de 64 bits y Pillow 9.5.0 con libtiff; no certifica soporte ni rendimiento |
| `pruebas` | Aprobadas, fallidas, errores y omitidas por separado, con motivo de cada omisión |
| `etapas` | Suite, creación de demo, diagnóstico, respaldo, verificación, restauración, conservación de la base y ventanas de la app y del asistente si se solicitaron |
| `comprobaciones_automaticas_correctas` | Todas las etapas solicitadas terminaron correctamente |
| `revision_manual_pendiente` | Comprobaciones físicas que el programa no puede decidir |
| `produccion_validada` | Siempre `false`: esta herramienta nunca abre ni certifica producción |

Se guardan registros `.log` UTF-8, `pruebas.json`, `demo/`, `respaldo/` y `restaurado/` dentro del destino. Las pruebas unitarias y gráficas usan además carpetas temporales del sistema, con contenido sintético, que eliminan al terminar normalmente. Nada se envía a servicios externos. Si falla una etapa, el comando termina con código distinto de cero y conserva el informe para revisarlo.

Ocho pruebas históricas de fuentes privadas están desactivadas de forma predeterminada. Algunas pruebas de enlaces simbólicos se omiten en Windows por los permisos que exige crearlos. Lee los motivos: una omisión no cuenta como aprobada. El ensayo y `tools/run_tests.py` desactivan expresamente la integración privada aunque una variable del equipo la habilite. La suite general solo la habilita con `DIGITALIZACION_PROBAR_FUENTES_PRIVADAS=1` y fuentes presentes; no hace falta para este ensayo y no debe habilitarse con expedientes reales sin autorización.

## Revisión humana después del ensayo

Abre la demo desde el mismo cmd.exe:

```bat
.venv\Scripts\python.exe main.py --workspace "C:\PruebasDigitalizacion\ensayo062\demo"
```

Comprueba los tres expedientes ficticios y los dos legajos de la misma identidad. Abre Codificar, cambia de archivo y de página. Prueba números de uno, dos y tres dígitos con Ctrl; con Ctrl+Shift para HL. Revisa teclado español, teclado numérico, foco en formularios, rueda, zoom, recorte y Cancelar. Retira/restaura un TIFF y resuelve el reescaneo de prueba; después organiza para actualizar las métricas.

Registra localmente operador, fecha, resultado, fallos y tiempos. Los TIFF pequeños de la demo no representan el rendimiento de documentos grandes en 3 GB. Completa esa revisión con muestras ficticias de tamaño representativo. Solo después procede con el respaldo, actualización y comparación de oficina descritos en [WINDOWS7.md](WINDOWS7.md).

## Repetir en este Mac

En Terminal, elige otro destino si ya existe:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python tools/ensayo_oficina.py --destino ensayos/nuevo-ensayo --ventanas
.venv/bin/python main.py --workspace ensayos/nuevo-ensayo/demo
```

Aquí `perfil_windows7_coincide` será `false`, aunque las pruebas pasen. No copies la `.venv` del Mac al equipo de oficina.

## Escenarios del modelo operativo

La demo incluye una recepción parcial resuelta, asignación, dos entregas de un ciclo y una observación respondida pendiente de validar. El ensayo gráfico comprueba además 360, préstamo, las cinco columnas del Kanban y evidencia de entrega; Codificación se verifica en 860, 1024 y 1366 píxeles, con las tres vistas y miniaturas virtuales. Estas comprobaciones no sustituyen la revisión de legibilidad, escalado, teclado ni rendimiento en el equipo de oficina. Sigue la secuencia humana del [manual vigente](MANUAL_USUARIO.html).

## Listas y legajos de 0.6.1

Sigue [IMPORTACION_FOLIOS_V06.md](IMPORTACION_FOLIOS_V06.md) con `demo/ejemplos/lista_folio_sintetica.csv`. El smoke gráfico automatizado comprueba importación, tres legajos, catálogos desde formularios anidados y filtros parciales sin reconstruir el Kanban. Revisa manualmente también encabezados de tus formatos, comodidad de búsqueda y legibilidad en la resolución real de la oficina. No uses datos productivos en una demo de libre distribución.

## Recepción e indicadores 0.6.1

El smoke incluye selección múltiple, vista previa/Cancelar/aceptación sin recaptura, legajos existentes y pendientes, cifras de barras dentro del canvas en 880/1024/1366 píxeles, filtro sin resultados, detalle y exportación BI. El filtrado/redimensionado no relee TIFF ni reconstruye Kanban. Prueba manual sugerida: [RECEPCION_INDICADORES_V061.md](RECEPCION_INDICADORES_V061.md).
