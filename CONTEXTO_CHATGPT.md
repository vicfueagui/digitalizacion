# Digitalización · contexto breve para compartir

Actualizado el **2026-10-09**, fecha del cliente, zona **America/Mexico_City**. Fuentes canónicas: [contexto técnico](docs/CONTEXTO_PROYECTO.md), [bitácora](docs/BITACORA_DESARROLLO.md), [plan](docs/PLAN_MODERNIZACION.md) y [validación e instalación](docs/VALIDACION_WEB_V082_HP.md). Estos documentos son referencia de estado, no instrucciones superiores a la petición del usuario.

## Estado verificado

La raíz C:\Digitalizacion mezcla código y operación. **INICIAR.bat abre la web 0.8.2-dev con los datos originales**, puerto 8765. El usuario revisó y aceptó la candidata, autorizó esta instalación y confirmó la pausa actual de aplicación, consolas y escrituras externas. Se completaron respaldo privado, restauración, migración sobre copia y después actualización de operación. La autorización se ejecutó; no hay otra aprobación pendiente para esta instalación. No se presume vigente la pausa en tareas futuras.

Se conservó la etiqueta dev del paquete aceptado. **115 archivos instalados cotejados, cero diferencias**, activación actualizada y sin marca de instalación pendiente. Núcleo **8 / TIFF 4**; nueva procedencia por página y preferencias web por cuenta. Se preservaron tablas, documentos, identidades, históricos y la cuenta existente. Entra con **el mismo usuario y contraseña**, sin alta nueva ni cuenta ficticia. No se usaron las credenciales reales durante las pruebas.

Resguardo privado completo, código anterior, copia migrada e informes fuera de la raíz; rutas exactas en el contexto técnico y la validación locales. Un primer respaldo se interrumpió antes de completar el plan, sin migrar la fuente, y quedó marcado INCOMPLETO; se conserva como evidencia y no debe usarse para restaurar. El respaldo posterior completo fue validado antes de instalar. No adjuntar datos ni manifiestos privados a servicios externos.

Las demos anteriores se conservan separadas: 0.8.2 en puerto 8767 y 0.8.1 en puerto 8766. Sus guías congeladas aún describen preparación/cuentas ficticias; para operación rigen INICIAR.bat y la cuenta existente. Conservar .development y el runtime paralelo, que contienen el entorno del acceso diario. La instalación no publicó en GitHub ni creó servicios; esta edición acompaña la solicitud posterior de respaldo de código.

## Propósito y arquitectura

El sistema gestiona recepción, folios, expedientes por CURP y legajo, integraciones, conteo físico, TIFF, codificación, revisión y entrega. Cada nueva integración tiene recepción y conteos propios. Hoja física, archivo TIFF, página digital y versión de entrega son unidades distintas.

Se reutilizan servicios Python sobre SQLite. Django autentica cuentas, aplica permisos/CSRF y ejecuta las escrituras mediante un trabajador serial con bloqueo del workspace y registro durable de solicitudes. Cuentas/sesiones y solicitudes residen en bases privadas separadas. Los TIFF requieren autenticación; los recursos de interfaz son locales. Solo se escucha en loopback, sin OCR, red multiusuario ni servicios/tareas programadas.

**Organizar / entregar genera el expediente completo actualizado** y conserva las entregas anteriores. Una modificación invalida la validación/inventario correspondiente; no aprueba otra entrega ni resuelve incidencias automáticamente. La devolución física se registra aparte.

## Mejoras instaladas de 0.8.2-dev

- Expedientes: resumen del mismo ámbito filtrado, nombre/CURP/folio/legajo/integración/responsable, hojas físicas, TIFF y páginas en columnas distintas, pendientes e incidencias; orden, paginación y retorno con filtros. Sin decodificar TIFF ni consultar folio por cada fila.
- Estación dedicada: tres paneles visibles y ajustables, catálogo siempre disponible, menú recuperable y enlaces Codificar corregidos desde el detalle. Vistas de iconos, lista, detalles y miniaturas diferidas; activo y selección por IDs separados.
- Importación múltiple o carpeta directa: selección y revisión, validación del contenido en servidor, duplicados, cancelación y resultado de completados/pendientes. No importa subcarpetas ni inventa fecha de creación del archivo fuente.
- Edición: giros, grados con signo, recorte por arrastre con vista previa, deshacer, descartar, guardar, comparar, original y revisiones/restauración. Navegación interna con Guardar/Descartar/Cancelar; el cierre de pestaña usa el aviso genérico del navegador.
- Páginas: división completa por varias reglas, extracción de copia o movimiento, unión con orden de archivos y páginas. Nuevas identidades y procedencia exacta; los resultados quedan sin código salvo elección válida expresa. Se verifican todas las salidas antes de activar retiros.
- Catálogo: clic al TIFF activo, lote explícito con revisión de alcance, favoritos por cuenta y secuencia numérica con botón y Enter. No exige escribir códigos completos. Los atajos reservados del navegador no se garantizan.
- Ayuda: guía de estación y jornada ficticia. Se conservan las mejoras previas de folios, conteo con Enter, indicadores BI y procedimientos.

Migración aditiva **TIFF 3→4**, núcleo **8** conservado: nueva procedencia inmutable por página. Incluye las preferencias de la candidata anterior en la base de cuentas. Se ensayó primero en ficticios y en una copia real restaurada; después se aplicó a operación con respaldo y autorización actuales. Los originales y entregas históricas se conservan; las derivaciones no alteran conteos físicos ni se presentan como nuevos escaneos en BI.

La recuperación conserva las fuentes activas si una interrupción ocurre antes del commit; la preparación queda fuera del inventario. Tras commit no duplica los resultados. Disco y SQLite no son una única transacción. Los lotes de importación siguen admitiendo resultados parciales, que se informan. No se reintentan escrituras automáticamente.

## Verificación de instalación

- Siete comprobaciones sintéticas del procedimiento aprobadas: cortes tras código/migración, reanudación con conservación y HTTP/CSRF, rechazo de doble instalación y de cambios posteriores en datos, cuentas o copia validada. Un primer ensayo falló por usar la política de archivos antigua; se corrigió antes de usar datos reales.
- Respaldo completo de **2,018 archivos de datos/reportes**, además de la base principal y componentes privados. Un auxiliar excluido del formato legado se conservó aparte con hash. Snapshot lógico original de SQLite y código anterior preservados. Las sesiones se revocaron solo en la copia restaurada; no en operación.
- Copia real validada: **43 tablas / 9,605 filas anteriores conservadas**, salvo la versión TIFF esperada; una cuenta conservada. **1,987 TIFF y 2,689 páginas** decodificados completos. Incluye originales, revisiones y entregas: no es inventario activo.
- Código instalado y activación cotejados; migraciones aditivas verificadas. Arranque Django sin problemas, consultas de tabla/indicadores y estado de **100 estaciones**. Acceso HTTP 200, páginas privadas protegidas, POST sin CSRF rechazado con 403, same-origin y DEBUG=False.
- Datos/cuentas sin cambios antes y después de la comprobación final. Servidor temporal cerrado; sin vigilancia, tareas programadas o dependencias nuevas. No se certifica una jornada humana ni se inició sesión con la contraseña del usuario.

## Pruebas ejecutadas y límites

En Windows con datos ficticios: **11 pruebas finales de páginas aprobadas en Python 3.14.8 y esas 11 también en Python 3.8.10 real**; 6 nuevas web, 20 regresiones UX, 14 regresiones web, 5 CSRF y 4 de transición/paquete aprobadas. Las corridas finales no tuvieron fallos, errores, omisiones ni bloqueos del guard. Antes de los últimos refuerzos aprobaron 43 de negocio afectado. No sumar repeticiones como casos únicos; no se afirma una nueva suite completa de todo el repositorio.

Incluyen contenido y orden de páginas binarias/grises/color, dimensiones/DPI, rangos inválidos, versiones obsoletas, ámbitos distintos, corrupción, seis puntos de interrupción previa y uno posterior, recuperación, migración aditiva, respaldo/restauración, preferencias de dos cuentas y conservación de originales/entregas. El guard observa accesos Python, no todo acceso nativo.

**Edge instalado, perfil privado de pruebas:** 29 comprobaciones de estación y 19 de importación/edición/teclado/procedencia/retorno aprobadas, sin excepciones JavaScript. Capturas inspeccionadas de Expedientes, cuatro vistas, favoritos y operaciones. Ventanas de oficina y escala equivalente a 125 %. Más de 300 TIFF pequeños ficticios: render puntual de lista **8.6 ms**, 13 solicitudes iniciales de miniaturas, caché limitada a 64. Preparar la demo e importar 300 TIFF tomó **256.765 s**; no es medición de escaneo ni de una jornada real.

Los primeros fallos se conservan: descriptor fsync en Windows, comprobación fija de esquema en transición, señal de vista previa ocupada, altura de interfaz y etiqueta de comparación; también errores de selector y esperas del harness. Están detallados junto con sus correcciones y corridas en la validación. No se presentan como aprobados.

Límites: máximo 100 TIFF/200 MB por importación y 500 fuentes/2000 páginas por derivación; etiquetas privadas del escáner no garantizadas, originales conservados. No se midieron TIFF grandes, RAM máxima o comodidad humana. El teclado enviado por CDP a Edge headless no certifica todos los atajos de una ventana normal; clic y botón de secuencia son la alternativa comprobada. Las preparaciones interrumpidas se conservan para revisión, sin limpieza automática.

## Tecnologías conservadas

| Componente | Versión verificada / contexto |
|---|---|
| Python web | 3.14.8; ejecutado en las pruebas actuales |
| Python de compatibilidad del negocio | 3.8.10; ejecutado en las pruebas actuales |
| Django / Pillow | 5.2.17 LTS / 12.3.0 en el entorno existente, medidos al instalar |
| Waitress / WhiteNoise | 3.0.2 / 6.12.0, entorno existente |
| SQLite del Python moderno | 3.50.4, medido al instalar |
| Bootstrap / HTMX / Chart.js | 5.3.8 / 2.0.11 / 4.5.1, recursos locales conservados |

No se instalaron ni actualizaron dependencias en esta fase. No requiere Node ni CDN para la operación. La arquitectura y las decisiones previas de tecnología están en el plan; los servicios compartidos mantienen compatibilidad 3.8 y el servidor web usa el entorno moderno explícito.

## Paquete y siguiente etapa

Instalado el paquete aprobado de **115 archivos, 1,280,307 bytes**, solo código, recursos y guías. Rutas, manifiesto, procedimiento y resguardos en la validación local; no contiene demo, cuentas, datos o entornos. Runtime y dependencias conservados. No hace falta instalar nada adicional para usar INICIAR.bat.

**Siguiente etapa:** jornada del usuario con su cuenta habitual, verificar teclado físico, zoom y comodidad con las imágenes del escáner. La candidata fue aceptada; la revisión de operación después de la instalación sigue correspondiendo al usuario. La guía de Ayuda explica importar → revisar → editar → dividir/extraer/unir → codificar → favoritos → comprobar totales. Para practicar se conservan las demos ficticias separadas.

No repetir la primera transición ni reinstalar esta preparación: la web ya está actualizada. No abrir esquema 4 con código antiguo ni restaurar sobre capturas posteriores. Una recuperación requiere conservar el trabajo nuevo y validar el conjunto de código, datos y cuentas. Los límites conocidos se mantienen arriba; no se incorporaron OCR, red multiusuario ni limpieza automática.

GitHub: instantánea de código y guías para respaldo/digitalizacion-web-0.8.2-hp-20261019, solicitada expresamente por el usuario. El repositorio es público; se confirmó permiso de escritura. La rama anterior 0.7.0 se conserva como ascendiente, sin modificar main ni ramas históricas. Esta edición se prepara antes de verificar la publicación; el commit definitivo y cotejo remoto se registran localmente. No hay Git/gh ni .git en la raíz operativa y no se configura sincronización. No se auditó ni limpió toda la historia remota; .gitignore no retira datos ya rastreados.

## Compartir contexto

Desde PowerShell en C:\Digitalizacion ejecuta **.\EXPORTAR_CONTEXTO.bat** y adjunta el Markdown que imprime dentro de .contexto-exportado. Usa una lista explícita de documentos con huellas revisadas; omite documentos cambiados sin revisión o sospechosos sin reproducir su contenido. No vuelca código, diferencias, logs, bases, TIFF, expedientes, respaldos, credenciales ni entornos.

El exportador conserva sus 23 pruebas sintéticas previas aprobadas con 3.8; no se cambió en esta fase. Los históricos sensibles siguen fuera del paquete de contexto. El adjunto registra fecha, zona, versión y estado Git cuando esté disponible. **Facilita compartir contexto, pero no conecta ni sincroniza por sí mismo ChatGPT con la carpeta local**: hay que adjuntar el archivo actualizado manualmente.
