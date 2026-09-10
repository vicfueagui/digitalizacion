# Arquitectura

## Enfoque

Monolito modular Django 5.2 LTS, renderizado del lado del servidor y JavaScript no obligatorio. SQLite permite iniciar sin servicios adicionales; la configuración admite PostgreSQL mediante variables de entorno.

Las capas son:

1. **Vistas y formularios**: autenticación, entrada y mensajes en español.
2. **Selectores**: limitan consultas según el alcance del usuario.
3. **Servicios de dominio**: transacciones, bloqueos, estados, asignación, importaciones e inventario.
4. **Modelos y constraints**: integridad relacional, unicidad y catálogos.
5. **Auditoría**: evento estructurado adicional a los historiales específicos.

Las vistas no deciden transiciones ni confían en que un botón oculto sea autorización. Los servicios verifican permisos y, cuando hay riesgo de concurrencia, bloquean el expediente con `select_for_update()`.

## Módulos

| App | Responsabilidad |
|---|---|
| `core` | dashboard, base común y auditoría |
| `accounts` | inicialización idempotente de grupos/permisos |
| `people` | persona, CURP, sistemas y pertenencias |
| `sources` | archivo/fila oficial e importador `.xlsx` |
| `batches` | recepción, fuente asociada y conciliación del lote |
| `records` | expediente, custodia, conteos, incidencias y estados |
| `digitization` | sesiones, documentos, modalidades, TIFF, inventario y CSV BAT |
| `quality` | decisiones de revisión y snapshots verificados |
| `reports` | consulta operativa filtrada |

## Persistencia y archivos

- La base guarda metadatos y referencias; nunca blobs TIFF.
- Los Excel se conservan bajo `MEDIA_ROOT/source_imports/` junto con hash y filas normalizadas/originales.
- Los CSV del BAT conservan hash, nombre y payload de cada fila; no se usan para validar automáticamente.
- El contrato `ReadOnlyTiffStorage` desacopla el dominio del almacenamiento. Su adaptador local resuelve rutas debajo de `DIGITAL_REPOSITORY_ROOT`, impide rutas absolutas, `..` y enlaces que salgan de la raíz, lee TIFF y registra una ejecución. No mueve ni borra archivos.

`PayrollSourceImporter` permite agregar posteriormente un adaptador `.xls` sin incorporar esa lógica al dominio. `DocumentClassifier` define solamente el contrato de una sugerencia futura; no existe una implementación OCR/IA en el MVP.

## Seguridad

Autenticación obligatoria, CSRF, cookies HttpOnly, encabezado anti-framing, límites de carga y permisos backend. Las opciones HTTPS son configurables porque el entorno productivo aún no está definido. Los eventos de auditoría filtran claves sensibles conocidas y no almacenan contenido de archivos.

Los archivos en `MEDIA_ROOT` no se publican mediante las URLs de desarrollo. Este MVP no implementa descargas; cuando se agreguen, deberán autorizarse y auditarse expresamente.

## Producción pendiente

Antes de producción se requiere definir proxy TLS, secretos, PostgreSQL, respaldos, antivirus/cuarentena de cargas, servidor de estáticos, disponibilidad de Bootstrap sin Internet y monitoreo. Consulte `OPEN_QUESTIONS.md`.
