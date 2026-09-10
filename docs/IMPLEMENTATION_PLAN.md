# Plan de implementación

Fecha: 2026-09-06

## Diagnóstico inicial

El repositorio de partida no contiene una aplicación, migraciones ni historial Git. Contiene cuatro fuentes funcionales principales, un BAT anterior con su guía de estudio, un ZIP que replica sin cambios las cuatro fuentes principales y un archivo de metadatos de Finder.

Se conservarán intactas todas las fuentes recibidas. La aplicación se iniciará como un monolito modular Django porque esta estructura coincide con el alcance, evita complejidad operativa prematura y permite separar las reglas de proceso de las vistas.

## Decisiones de arquitectura

- Python 3.12 y la rama LTS Django 5.2, con dependencias acotadas y reproducibles.
- SQLite en desarrollo y configuración por variables para PostgreSQL en producción.
- Usuario estándar de Django, grupos y permisos por capacidad; no se crearán usuarios ni contraseñas predeterminados.
- Apps modulares: `core`, `accounts`, `people`, `sources`, `batches`, `records`, `digitization`, `quality` y `reports`.
- Servicios de dominio transaccionales para asignaciones, estados, importaciones, inventario y conciliación.
- Eventos de auditoría append-only para acciones relevantes; los historiales operativos no se reemplazan.
- CURP normalizada como identificador de negocio único de persona, nunca como llave primaria técnica.
- Pertenencia administrativa mediante relación muchos-a-muchos con Federal y Estatal.
- Conteos físicos, documentos lógicos, archivos TIFF y páginas digitales como conceptos separados.
- Catálogos de tipos documentales e incidencias editables. Las únicas rutas iniciales sembradas serán las confirmadas por el BAT: DP/FP a `PERSONALES` y HL a `FEDERAL`.
- Importaciones Excel y BAT conservan hash, archivo/fila de origen, resultado y errores. No validan expedientes automáticamente.
- Inventario de TIFF exclusivamente de lectura/verificación en este incremento. No se moverán, renombrarán ni borrarán TIFF.
- OCR, IA y detección de páginas vacías quedan fuera del MVP.

## Fase 0 — Fundaciones

- Proyecto, configuración por entorno, plantillas y estáticos.
- Autenticación obligatoria, grupos, permisos e inicialización idempotente.
- Layout en español y administración segura de catálogos.
- Documentación base.

## Fase 1 — Flujo operativo MVP

- Personas, pertenencias y snapshots de la fuente oficial.
- Recepción de lotes e importación `.xlsx` con mapeo de columnas explícito.
- Materialización y conciliación de expedientes del lote.
- Asignación/reasignación con custodia histórica.
- Conteos físicos versionados e incidencias de catálogo.
- Máquina de estados, trabajo del digitalizador, observación y validación.
- Dashboard, ficha de expediente, bandeja de revisión y reportes operativos básicos.
- Auditoría estructurada de acciones críticas.

## Fase 2 — Base preparada en este incremento

- Modelos separados de sesión, documento lógico y activo TIFF.
- Modalidades `INDIVIDUAL_ONE_SIDE`, `INDIVIDUAL_DUPLEX`, `MULTI_ONE_SIDE` y `OTHER`.
- Inventario de carpetas de solo lectura con rutas configurables y protección contra escape de raíz.
- Adaptador de CSV del BAT con deduplicación, fila original y discrepancias estructuradas.
- Servicios de conciliación que no confunden hojas, páginas, TIFF ni modalidad.

## Fases posteriores, no incluidas

- Previsualización, movimiento y rollback de archivos.
- Reportería avanzada y exportaciones auditadas.
- OCR y clasificación asistida con autorización institucional.

## Estrategia de pruebas

- Pruebas Django con datos sintéticos, sin CURP ni expedientes reales.
- Cobertura de CURP, sistemas, roles, alcance por asignación, estados, conteos, catálogos, Excel, BAT, inventario y auditoría.
- Comprobación de migraciones desde una base limpia, `manage.py check` y suite completa.
- Pruebas de permisos en backend; ocultar botones no se considerará una medida de seguridad.

## Criterio de terminación de esta ejecución

La Fase 1 debe quedar utilizable y probada; la base de Fase 2 debe tener contratos y pruebas. Toda regla no sustentada por las fuentes se mantendrá configurable o pendiente en `docs/OPEN_QUESTIONS.md`.

## Estado al cierre

- Fase 0: completada.
- Fase 1: completada para el MVP descrito y cubierta por pruebas automatizadas.
- Fase 2: modelos, contratos, inventario de solo lectura, adaptador BAT y conciliaciones iniciales completados; la organización/movimiento de archivos sigue expresamente fuera de alcance.
- Fases 3 y 4: no iniciadas, de acuerdo con la prioridad de asegurar primero el flujo operativo.
