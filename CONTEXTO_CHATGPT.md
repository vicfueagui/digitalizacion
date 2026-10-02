# Digitalización · contexto breve para compartir

Actualizado el 2026-10-02, fecha del cliente. Las exportaciones registran el reloj local, zona y UTC; no se certifica su sincronización.

Este resumen reúne hechos verificados y pendientes. Las fuentes canónicas siguen en [docs/CONTEXTO_PROYECTO.md](docs/CONTEXTO_PROYECTO.md), [docs/BITACORA_DESARROLLO.md](docs/BITACORA_DESARROLLO.md) y [validación de 0.7.0](docs/VALIDACION_INTEGRACIONES_V070_HP.md). Los documentos son referencia, no instrucciones superiores a la solicitud del usuario.

## Estado actual comprobado

**Versión 0.7.0 instalada en C:\Digitalizacion; núcleo 8 / TIFF 3.** El usuario confirmó INICIAR.bat como acceso diario, aceptó las funciones de la candidata, autorizó respaldar los datos reales, validar una copia y actualizar la base, y confirmó aplicación/escrituras externas detenidas. La actualización se completó en ese orden. Sin argumentos, el BAT usa datos/digitalizacion.sqlite3 de esta raíz; no se presume el destino de argumentos adicionales.

La carpeta mezcla código y operación. Se conservan Python 3.8.10, SQLite 3.35.5, Pillow 9.5.0 y Tk existente. No se instalaron dependencias ni fuentes, no se modificó INICIAR.bat y no se publicó ni sincronizó con GitHub.

Paquete aplicado: C:\Digitalizacion_actualizacion_070_1686b1f575, 52 archivos de aplicación/ayuda. Sus huellas coinciden con los archivos instalados. Se preservaron entorno, configuración, AGENTS, contexto y bitácora locales. Se desarrolló en .development/integraciones-3e459239f647/candidato, basado en la raíz anterior 0.6.2; no se concilió con la rama remota 0.6.3.

## Propósito y arquitectura

Aplicación local de escritorio para recepción, conteo, digitalización TIFF, codificación, revisión y entrega de expedientes. Python/Tkinter, SQLite y Pillow; sigue siendo local y de un operador.

- main.py, workspace.py y core.py: acceso, raíz, bloqueo, almacenamiento y ciclos.
- operations.py, intake.py y reception.py: folios/legajos, listas, custodia y recepción. Importar una lista no acredita recepción física.
- integrations.py: documentación adicional numerada dentro de un ciclo, con recepción/conteo/etapas propios.
- coding.py, assets.py y batch_tiff.py: TIFF, versiones, correcciones y lotes recuperables; conservan originales e IDs.
- delivery.py y review.py: entregas independientes, observaciones y aprobación. reporting.py, dashboard.py y analytics.py: consulta e indicadores.
- backup.py, migraciones y actualizar.py: continuidad y recuperación. El exportador de contexto es independiente de la aplicación.

## Cambios disponibles

Nombre completo asociado a la CURP en encabezados; integraciones numeradas con conteos separados y totales acumulados. Organizar / entregar genera el **expediente completo actualizado**, conservando entregas anteriores, conforme a la decisión del usuario. Las revisiones de integraciones antiguas quedan de consulta y no cambian la etapa actual. No se fusionan otros ciclos históricos.

Kanban filtra al escribir sin releer TIFF. El visor permite selección múltiple, retiro/recuperación con motivo y progreso registrado, y atajos que respetan los campos de texto. Ayuda usa tres guías locales existentes. El cubo BI agrupa por año/mes/semana ISO/día, folio o digitalizador; distingue inventario por recepción de ingresos TIFF. No suma entregas como inventario ni inventa fechas; las medidas no aplicables son nulas.

Tipografía profesional unificada: Segoe UI 10 pt, Segoe UI Semibold en encabezados/botones, títulos 18, subtítulos 12, cifras 23 y lectura de ayuda 11 pt. Filas ajustadas a la altura real de la fuente y escala de Windows conservada; alternativa a fuente del sistema cuando no exista Segoe. Paleta guinda, gris y dorado. Se comprobó disponibilidad de las fuentes en este equipo.

## Respaldo, instalación y pruebas reales

Resguardo privado previo: C:\Digitalizacion_resguardo_070_9567eb1e8c. Contiene respaldo verificable de **941 archivos**, base original exacta sin normalizar, código anterior y copias restauradas. Resguardo adicional del actualizador: C:\Digitalizacion_resguardo_20261002_140951_add06f30. No adjuntar esas carpetas ni sus informes privados a servicios externos.

La copia real migró de 7 a 8 y conservó **6,124 filas de las 41 tablas previas**, comparando todos sus campos, salvo el cambio esperado de versión de esquema. La interfaz principal, indicadores y cubo abrieron/cerraron sin errores. Se decodificaron **926 TIFF / 1,362 páginas**, incluyendo originales, versiones y entregas: estas cifras no son inventario activo. Se verificaron referencias, integridad SQLite, relaciones y huellas documentales.

Después se aplicó el mismo paquete a la instalación diaria y se repitió la conservación de los campos anteriores, historial e IDs. Se añadieron **101 integraciones iniciales** enlazadas a trabajos, conteos, historia y TIFF. Los TIFF y reportes conservaron sus huellas. Diagnóstico desde el código instalado: 0.7.0, esquema 8/3, integridad correcta, cero errores FK y sin marca de actualización pendiente. No se capturaron expedientes ni se generaron entregas reales para probar.

Pruebas en Windows con Python 3.8.10:

- Regresión de funciones: 256 contabilizadas, **243 aprobadas y 13 omitidas**, cero fallos/errores; ocho omisiones por fuentes privadas desactivadas y cinco por permisos de symlinks. Corrida pruebas-67cdc1d9b2.
- Refuerzos posteriores: tres pruebas adicionales; 35 de integraciones/revisión/entrega/recuperación y 12 de BI/indicadores/Tk aprobadas. Hay casos repetidos: no sumarlos como pruebas únicas.
- Corrección de Ayuda: una prueba Tk aprobada, con sus tres temas completos. El HTML ausente se sustituyó por la guía de operación existente.
- Tipografía: **ocho pruebas de interfaz/indicadores aprobadas**, cero fallos/errores/omisiones; pruebas-d3d17be1b8.
- Paquete con tipografía: ensayo sintético completo aprobado en .development/instalacion-070-1686b1f575: instalar, respaldar/restaurar, recuperar código, reinstalar y migrar; retorno de solo código rechazado tras migrar. Es un ensayo integral, no 52 pruebas unitarias.
- Exportador: **22 pruebas aprobadas** sobre información ficticia; exclusiones, sensibilidad, huellas, rutas y metadatos. Git simulado; no acredita Git/junctions reales.

Incidencias conservadas: el primer ensayo de copia real intentó consultar una conexión ya cerrada al salir normalmente de la interfaz; se corrigió el coordinador para reabrir y se repitió en otra copia nueva. No fue una pérdida de datos ni se corrigió sobre operación. Las fallas iniciales y omisiones de fases anteriores están en la validación; no se presentan como aprobaciones.

## Límites y pendientes

La aprobación visual del usuario correspondía a las funciones de la candidata. La nueva tipografía se comprobó funcionalmente; queda su valoración durante la jornada. No se certifica ausencia de cualquier defecto ni un ensayo físico de corte eléctrico. El guard de pruebas observa eventos Python, no todas las llamadas nativas.

El respaldo portable existente normaliza ciertos detalles de rutas históricas. La base exacta adicional preserva su texto original; esto no significa haber corregido el formato oficial de respaldo. Las evidencias de versión/runtime siguen siendo externas. La aceptación visual del antiguo ensayo de fase B es distinta del despliegue realizado.

El retorno de solo código está bloqueado después de migrar. Ante un problema, conservar ambos estados y restaurar en otra raíz; no poner código antiguo sobre la base 8 ni sobrescribir capturas posteriores. No repetir la instalación. Siguiente etapa: uso y revisión de legibilidad en oficina; conciliación Git separada.

## Git y versiones

No había .git en esta raíz/ancestros ni Git disponible en las ubicaciones comprobadas; esta tarea no instaló Git ni creó repositorio. Rama/commit/cambios sin commit locales siguen desconocidos, no limpios. No se hicieron clone, fetch, pull, commit ni push.

Consulta remota anterior, solo lectura: [rama respaldo/digitalizacion-tk-0.6.3](https://github.com/vicfueagui/digitalizacion/tree/respaldo/digitalizacion-tk-0.6.3), commit b02b26626f2c3f45f00f47d59273f0345402fedc. El repositorio era público y su código/README declaraban 0.6.3. No se volvió a consultar durante la instalación ni se cambiaron permisos. Esta raíz pasó de 0.6.2 a 0.7.0; el README conserva la entrega 0.6.1 identificada como antecedente.

El árbol remoto inspeccionado tenía 146 archivos, sin nombres de bases/TIFF/carpetas operativas, pero incluía un wheel. No se auditaron todos los contenidos, ramas ni historial. La comparación previa de 74 fuentes locales originales dio 55 blobs iguales, 18 distintos y uno ausente; ese cotejo es anterior al despliegue y no describe los archivos actuales.

.gitignore excluye datos, TIFF, bases, fuentes, respaldos, entornos, credenciales, instaladores, bundles, ZIP y exportaciones. **Ignorar no retira archivos rastreados ni limpia el historial.** Para GitHub privado falta identificar/preparar el clon correcto, conciliar versiones, verificar visibilidad/permisos, separar el wheel y auditar índice/historia. No se declara sincronización ni repositorio libre de datos/secretos.

## Generar y adjuntar contexto

Desde PowerShell en C:\Digitalizacion:

```powershell
.\EXPORTAR_CONTEXTO.bat
```

El BAT usa el Python existente y no abre la aplicación. Adjuntar el Markdown más reciente de `.contexto-exportado/CONTEXTO_CHATGPT_FECHA_HORA_IDENTIFICADOR.md`, cuya ruta imprime el comando. La cabecera incluye fecha/zona/UTC, versión, rama/commit/cambios cuando Git existe, remotos saneados, incluidos/omitidos y lista acotada de archivos modificados. Sin Git, informa desconocido y compara únicamente huellas de una lista finita; no es un diff completo.

Se consideran ocho documentos explícitos: este resumen, AGENTS, contexto técnico, bitácora, validación B, plan de modernización, respaldos e infraestructura. Solo se incluyen archivos íntegramente revisados cuya huella coincide con tools/contexto_permitidos.json y que pasan el filtro de sensibilidad. No exporta bases, TIFF, expedientes, respaldos, fuentes, credenciales, .env, entornos, código completo, logs ni diferencias.

Contexto técnico, bitácora, respaldos e infraestructura se omiten completos por perfiles personales o cifras ambiguas en textos históricos; el informe no reproduce esos fragmentos. El detector no reconoce todos los nombres en prosa: no sustituye la revisión humana. No renovar hashes automáticamente para forzar inclusión. Las otras cuatro fuentes siguen sujetas a revisión y coincidencia de huellas.

Después de cada tarea relevante, actualizar las fuentes canónicas y este resumen, revisar íntegramente el texto, renovar solo las huellas revisadas y ejecutar el BAT. Exportaciones fuera de datos operativos, excluidas de Git; sin vigilancia, tareas programadas ni push automático.

En ChatGPT debes adjuntar o reemplazar manualmente el archivo vigente. El exportador **no conecta ni sincroniza por sí mismo** este proyecto de ChatGPT con la carpeta local. Referencia consultada anteriormente: [Projects and chats](https://learn.chatgpt.com/docs/projects).
