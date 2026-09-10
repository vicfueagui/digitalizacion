# Prompt para Codex/Windsurf — Inicio profesional del Sistema de Digitalización SEGEY

Actúa como **arquitecto de software senior, desarrollador Django senior, analista de procesos y diseñador de sistemas administrativos auditables**. Debes iniciar o adaptar un proyecto real para apoyar la digitalización de expedientes de personal del Archivo General de la Secretaría de Educación del Estado de Yucatán (SEGEY).

Tu prioridad no es construir muchas pantallas rápidamente. Tu prioridad es crear una **base correcta, mantenible, auditable y fácil de usar**, que permita crecer después hacia automatización de TIFF, OCR y clasificación asistida por IA sin rehacer el núcleo del sistema.

## 1. Antes de modificar código

1. Inspecciona completamente la carpeta del proyecto actual.
2. Si el repositorio ya contiene código, documentación, migraciones o decisiones previas, **no lo reemplaces ni lo reinicialices**. Analiza primero arquitectura, dependencias, modelos, tests y estado de Git.
3. Si la carpeta está vacía, inicializa el proyecto de manera limpia.
4. Busca y lee, si están presentes, estos archivos de contexto:
   - `CONTEXTO_SISTEMA_DIGITALIZACION_SEGEY.md`
   - `GUIA_BAT_V2_PRINCIPIANTES.md`
   - `organizar_tiff_por_curp_v2.bat`
   - cualquier BAT, guía, Excel de ejemplo o documento del proyecto relacionado con digitalización.
5. Considera esos archivos como **fuentes funcionales del proyecto**. No inventes reglas de negocio cuando la fuente no las defina.
6. Si detectas contradicciones entre fuentes, no elijas silenciosamente una versión: documenta la contradicción en `docs/OPEN_QUESTIONS.md` y diseña la solución para que la regla pueda configurarse.
7. Antes de implementar, crea o actualiza `docs/IMPLEMENTATION_PLAN.md` con las decisiones tomadas y las fases de trabajo.

## 2. Entorno de desarrollo

El proyecto se desarrollará principalmente con Codex dentro de Windsurf en una MacBook Pro con macOS 11.7.11.

Preferencias técnicas iniciales:

- Python 3.12, si está disponible de forma estable en el equipo.
- Django 5.2 LTS, usando el último parche disponible de la rama 5.2.
- SQLite para desarrollo local inicial.
- Preparar configuración para PostgreSQL en producción, sin obligar a instalar PostgreSQL para poder comenzar.
- Django Templates con renderizado del lado del servidor.
- Bootstrap para una interfaz clara y responsive, evitando un frontend SPA innecesario.
- JavaScript mínimo y progresivo.
- `openpyxl` para importación `.xlsx` cuando corresponda.
- Pillow o librería TIFF solamente cuando realmente se implemente inspección de imágenes; no añadir dependencias pesadas sin uso.
- `pytest` o el framework de pruebas estándar de Django, pero mantener una estrategia consistente en todo el repositorio.
- Variables sensibles en `.env`; proporcionar `.env.example` sin secretos.

No conviertas este proyecto en microservicios. Para esta etapa utiliza un **monolito modular Django** con capas claras y servicios de dominio donde las reglas de negocio lo justifiquen.

No dependas de que Python esté instalado en cada computadora de los digitalizadores. La meta futura es que los usuarios operativos utilicen el sistema desde un navegador dentro de la red autorizada.

## 3. Objetivo funcional

El sistema debe dar trazabilidad desde que un lote de expedientes llega al área de digitalización hasta que el trabajo del digitalizador es revisado y validado por el responsable.

Debe ayudar a controlar:

- lote recibido;
- archivo Excel entregado como referencia;
- expediente físico;
- persona/empleado;
- pertenencia Federal, Estatal o ambas;
- asignación del expediente;
- custodia/responsable actual;
- conteo de hojas físicas;
- incidencias;
- proceso de digitalización;
- cantidad de archivos TIFF;
- modalidad INDIVIDUAL/MULTI;
- clasificación documental por catálogo;
- estructura de carpeta CURP;
- conciliaciones automáticas;
- cierre del trabajo por digitalizador;
- validación/observación por responsable;
- historial y auditoría.

## 4. Regla conceptual obligatoria

Modela como conceptos diferentes:

1. **Hoja física**: pieza de papel.
2. **Página digital**: cara/página contenida en un archivo digital.
3. **Archivo TIFF o digital**: archivo `.tif`/`.tiff`.
4. **Documento lógico**: documento administrativo que puede tener una o varias hojas/páginas.

No utilices una sola columna llamada `cantidad` para representar conceptos distintos.

Nunca supongas que:

`1 hoja física = 1 página digital = 1 TIFF`.

Eso no es cierto en este proceso.

## 5. Modalidades de escaneo

El sistema debe poder representar desde el inicio al menos:

- `INDIVIDUAL_ONE_SIDE`: individual una cara.
- `INDIVIDUAL_DUPLEX`: individual doble cara / modalidad conocida operativamente como METLIFE.
- `MULTI_ONE_SIDE`: documento multi una cara, pudiendo incorporar páginas adicionales cuando una hoja necesite segunda cara.
- `OTHER`: reservado para modalidades futuras, acompañado de descripción cuando se use.

Además, para reportes operativos debe existir una agrupación simple:

- `INDIVIDUAL`
- `MULTI`

Regla crítica:

**Un TIFF con más de una página no debe clasificarse automáticamente como MULTI.** Un TIFF individual de doble cara puede tener dos páginas.

Si posteriormente se calcula `page_count`, ese dato debe almacenarse separado de `scan_mode`.

## 6. Sistemas Federal y Estatal

Una persona puede pertenecer:

- únicamente a Federal;
- únicamente a Estatal;
- a ambos.

No implementes esto como un booleano mutuamente excluyente.

Crea un catálogo/modelo de sistemas administrativos y una relación que permita múltiples pertenencias, con historial o snapshots cuando sea necesario.

El flujo actual del área descrita trabaja principalmente con Federal, pero el modelo no debe impedir ampliar posteriormente a Estatal.

La presencia de documentación Estatal en un expediente Federal debe poder registrarse como incidencia, no eliminarse silenciosamente.

## 7. Datos oficiales y Excel

Nóminas funciona como fuente oficial de datos de referencia del empleado.

Diseña una importación auditable de Excel:

- registrar archivo fuente;
- nombre original;
- fecha de importación;
- usuario que importó;
- hash SHA-256 del archivo fuente;
- número de filas;
- filas aceptadas;
- filas con error;
- advertencias;
- mapeo de columnas;
- valores originales relevantes o un `raw_payload` por fila para trazabilidad.

No sobrescribas silenciosamente la historia cada vez que llegue un nuevo Excel. Debe ser posible conocer qué datos eran los recibidos en un lote determinado.

Implementa primero `.xlsx`. Si aparecen archivos `.xls`, diseña el importador como adaptador para poder agregar soporte después sin mezclarlo con la lógica del dominio.

La importación debe detectar al menos:

- CURP vacía;
- CURP con formato evidente inválido;
- CURP duplicada dentro del mismo archivo;
- filas duplicadas;
- expediente físico sin fila correspondiente;
- fila sin expediente recibido, cuando el usuario haga la conciliación;
- contradicciones de sistema Federal/Estatal cuando existan datos para detectarlas.

No inventes nombres de columnas del Excel real. Crea un mecanismo de mapeo configurable y documenta que debe ajustarse cuando se entregue un archivo de ejemplo real.

## 8. Modelo de dominio mínimo sugerido

Adapta los nombres si el proyecto existente ya tiene convenciones, pero cubre estos conceptos.

### Accounts / seguridad

- `User`
- Groups / Roles
- permisos granulares

No escribas lógica como `if username == "admin"`.

### Person / Employee

Representa a la persona sin usar la CURP como primary key técnica de todas las relaciones.

Campos mínimos aproximados:

- id interno;
- CURP normalizada;
- nombre cuando la fuente lo proporcione;
- estado activo/inactivo si la fuente lo proporciona;
- timestamps.

### AdministrativeSystem

Catálogo como:

- FEDERAL
- STATE / ESTATAL

### PayrollImport / SourceBatch

Representa cada archivo de fuente oficial y sus filas/snapshots.

### IntakeBatch / DigitizationBatch

Representa el lote de expedientes físicos entregado al responsable de digitalización.

Debe registrar:

- identificador;
- fecha de recepción;
- responsable que recibe;
- archivo oficial asociado;
- cantidad esperada de expedientes;
- observaciones;
- estado del lote.

### PersonnelRecord / Expediente

Representa el expediente físico/digital en proceso.

Debe permitir:

- persona;
- lote;
- sistemas declarados;
- sistema esperado para el trabajo actual;
- identificador físico si existe;
- estado de flujo;
- ubicación/custodia actual;
- conteos resumidos derivados, sin duplicar datos cuando puedan calcularse.

### RecordAssignment

Historial de asignaciones del responsable al digitalizador.

Nunca conserves únicamente `assigned_to` si eso borra la historia. Puede existir un campo actual para rapidez, pero debe coexistir con historial auditable.

### PhysicalCount

Registro de conteo físico:

- expediente;
- cantidad de hojas físicas;
- usuario;
- fecha/hora;
- versión/reconteo;
- motivo cuando se corrige un conteo anterior.

No borres el conteo anterior al corregirlo.

### IncidentType

Catálogo administrable:

- código;
- nombre;
- descripción;
- categoría;
- severidad;
- bloquea_flujo;
- activo;
- vigencia.

No hardcodear el catálogo provisional.

### Incident

Incidencia concreta del expediente:

- tipo;
- expediente;
- etapa en la que se detectó;
- descripción/nota;
- detectado por;
- fecha/hora;
- estado;
- resolución;
- resuelto por;
- fecha de resolución.

### DocumentType

Catálogo de tipos documentales.

Debe soportar, inicialmente como datos configurables:

- `DP`
- `FP`
- `HL`

Campos sugeridos:

- code;
- name;
- description;
- destination_folder;
- applicable_systems;
- active;
- sort/order;
- effective dates si aplica.

Las reglas actuales del BAT son:

- DP y FP → `PERSONALES`
- HL → `FEDERAL`

Carga estas reglas mediante una migración de datos, fixture o comando idempotente, no repitiendo strings en diferentes vistas/servicios.

### ScanSession

Representa una sesión de trabajo del digitalizador sobre un expediente.

Debe permitir:

- inicio;
- fin;
- digitalizador;
- scanner/workstation opcional;
- observaciones;
- estado.

### DigitalDocument / DocumentRecord

Representa el documento lógico identificado por el digitalizador.

Debe contener:

- expediente;
- tipo documental confirmado;
- modalidad de escaneo;
- agrupación individual/multi;
- orden dentro del expediente si se conoce;
- usuario que confirmó la clasificación;
- fecha/hora.

### DigitalAsset / TiffAsset

Representa cada archivo TIFF real.

Campos sugeridos:

- expediente;
- documento lógico opcional;
- filename;
- relative_path;
- extension;
- file_size;
- sha256;
- page_count nullable;
- detected_prefix;
- status;
- discovered_at;
- last_verified_at.

No guardes archivos TIFF grandes dentro de la base de datos como blobs salvo que exista una razón documentada. Guarda referencia de almacenamiento y metadatos.

### QualityReview

Revisión del responsable/revisor:

- expediente;
- revisor;
- fecha/hora;
- decisión;
- observaciones;
- conteos verificados;
- discrepancias encontradas.

### AuditEvent

Bitácora de acciones relevantes.

Debe registrar de forma estructurada:

- actor;
- acción;
- entidad;
- id entidad;
- fecha/hora;
- valores anteriores/nuevos cuando sea apropiado;
- contexto/motivo.

Evita crear una bitácora genérica que almacene contraseñas, tokens o archivos completos.

## 9. Estados del expediente

Implementa una máquina de estados clara en una capa de servicio, no transiciones arbitrarias desde cualquier vista.

Estados iniciales sugeridos:

- `RECEIVED`
- `ASSIGNED`
- `IN_PROGRESS`
- `READY_FOR_REVIEW` — mostrar en interfaz como “Terminado por digitalizador / Pendiente de validación”.
- `OBSERVED`
- `CORRECTED`
- `VALIDATED`
- `CLOSED`
- `CANCELLED` solamente con permisos y motivo.

Reglas mínimas:

- un digitalizador no debe cerrar un expediente que no le esté asignado;
- cerrar el trabajo no equivale a validarlo;
- `VALIDATED` requiere un usuario con permiso de revisión/supervisión;
- una observación debe quedar histórica;
- una corrección no debe borrar la observación original;
- toda transición importante debe auditarse.

## 10. Roles y permisos iniciales

Crea Groups y permisos idempotentes mediante una migración de datos o comando de inicialización.

### Administrador

Puede administrar todo, incluyendo usuarios, roles, catálogos y configuración.

### Responsable de digitalización / Supervisor

Puede:

- recibir lotes;
- importar Excel;
- conciliar lote;
- asignar/reasignar expedientes;
- consultar todos los expedientes del área;
- revisar productividad;
- observar/validar;
- consultar auditoría operativa;
- administrar ciertos catálogos funcionales si se le concede el permiso específico.

No debe recibir automáticamente permisos técnicos de superusuario.

### Digitalizador

Puede:

- ver expedientes asignados;
- aceptar/iniciar trabajo;
- registrar físicos;
- registrar incidencias;
- registrar documentos y modalidad;
- vincular/ver inventario TIFF del expediente;
- cerrar su trabajo y enviarlo a revisión.

No puede validar su propio expediente salvo que se le otorgue explícitamente otro rol y la política lo permita.

### Revisor / Control de calidad

Puede:

- consultar expedientes enviados a revisión;
- comparar conteos;
- registrar observaciones;
- aprobar/validar según permiso;
- consultar evidencia e historial.

No administra usuarios ni configuración general.

### Consulta / Auditoría

Solo lectura de los módulos autorizados, reportes e historial.

Implementa permisos por capacidad. El sistema debe permitir editar posteriormente qué permisos contiene cada grupo sin cambiar código de vistas.

## 11. Pantallas mínimas del MVP

Diseña interfaz en español, profesional y simple para personal no técnico.

### Dashboard

Según rol mostrar:

- lotes recibidos;
- expedientes pendientes de asignar;
- expedientes en proceso;
- terminados por digitalizador pendientes de revisión;
- observados;
- validados;
- alertas de conciliación;
- productividad básica del periodo.

No presentes un exceso de gráficas decorativas. Prioriza tarjetas accionables y tablas filtrables.

### Lotes

- listado;
- crear/recibir lote;
- asociar/importar Excel;
- conciliación de filas vs expedientes;
- asignación masiva o individual.

### Mis expedientes — Digitalizador

Tabla con:

- CURP;
- nombre si está disponible;
- sistema esperado;
- estado;
- físicos;
- digitales;
- incidencias;
- fecha asignada;
- acción siguiente.

### Ficha de expediente

Debe ser el centro de trabajo.

Secciones sugeridas:

1. Identificación y fuente oficial.
2. Sistemas Federal/Estatal.
3. Custodia/asignación.
4. Conteo físico e historial.
5. Incidencias.
6. Sesión de digitalización.
7. Documentos/tipos/modos.
8. Inventario TIFF.
9. Resumen de conteos.
10. Conciliaciones/alertas.
11. Historial.
12. Cierre/envío a revisión.

### Bandeja de revisión

Para responsable/revisor:

- pendientes;
- discrepancias;
- conteos físicos;
- total TIFF;
- individuales;
- multi;
- DP/FP/HL;
- archivos inesperados;
- incidencias;
- observaciones;
- validar / devolver para corrección.

### Catálogos

- tipos documentales;
- tipos de incidencia;
- sistemas;
- configuración funcional autorizada.

### Reportes iniciales

Filtros por fecha, lote, digitalizador, estado y resultado.

Mostrar como mínimo:

- expedientes trabajados;
- hojas físicas capturadas;
- archivos TIFF/digitales;
- individuales;
- multi;
- incidencias por tipo;
- expedientes observados;
- expedientes validados;
- diferencias de conciliación.

No uses estas métricas automáticamente como evaluación laboral punitiva. El sistema debe registrar datos operativos y contexto/incidencias; la interpretación administrativa corresponde a responsables autorizados.

## 12. Integración inicial con el BAT

El BAT v2 es una herramienta de transición.

El sistema debe poder convivir con él inicialmente.

Implementa una capa/adaptador para importar el `RESUMEN_DIGITALIZACION.csv` generado por una carpeta CURP o filas de `CONTROL_DIGITALIZACION.csv`.

La importación debe:

- validar CURP;
- detectar duplicados de importación;
- conservar la fila fuente;
- registrar quién importó;
- comparar físicos/digitales/individual/multi contra lo ya capturado;
- mostrar discrepancias;
- no cambiar a `VALIDATED` automáticamente.

No hagas que el sistema dependa permanentemente del BAT. Define una interfaz de servicios para que posteriormente el propio sistema pueda inventariar y organizar archivos.

## 13. Inventario de carpetas y TIFF

Diseña una abstracción de almacenamiento.

Configuraciones sugeridas:

- `SCANNER_INBOX_ROOT`
- `DIGITAL_REPOSITORY_ROOT`

No hardcodees rutas Windows como `C:\escaner` dentro de modelos o vistas.

Crea un servicio que en una fase inicial pueda:

- leer una carpeta CURP;
- inventariar `.tif` y `.tiff`;
- calcular total por carpeta;
- calcular total por prefijo;
- detectar TIFF sueltos;
- detectar nombres no reconocidos;
- calcular SHA-256 cuando se solicite;
- actualizar metadatos sin borrar historia.

Por seguridad, la primera implementación web debe ser **read/verify first**. No muevas ni renombres archivos desde la aplicación hasta tener tests, permisos, previsualización de cambios y una política de rollback/registro auditado.

## 14. Clasificación automática futura

No implementar IA/OCR como requisito del primer MVP.

Pero deja una interfaz limpia, por ejemplo un servicio `DocumentClassifier`, que en el futuro pueda devolver:

- `suggested_document_type`;
- `confidence`;
- `evidence`/señales utilizadas;
- versión del modelo;
- fecha.

Reglas:

- la predicción no sustituye la confirmación humana en la primera etapa;
- guardar sugerencia y decisión final por separado;
- registrar quién corrigió la sugerencia;
- nunca eliminar páginas por “parecer en blanco” automáticamente;
- hojas recicladas, rayadas o de baja calidad deben quedar disponibles para revisión humana.

## 15. Validaciones y conciliaciones

Crea servicios explícitos de conciliación.

Ejemplos:

- `physical_count_exists`;
- `source_row_matches_record`;
- `digital_total_matches_inventory`;
- `individual_plus_multi_equals_digital_total`;
- `prefix_counts_match_digital_total`;
- `unexpected_files_count`;
- `state_documents_in_federal_record` cuando sea detectable;
- `foreign_person_document` como incidencia humana, no como inferencia automática inicial.

Una discrepancia debe mostrarse como alerta estructurada y no esconderse detrás de un texto genérico.

## 16. Integridad de datos

Usa:

- constraints de base de datos cuando aplique;
- transacciones atómicas para cambios de estado/asignación;
- `select_for_update()` donde exista riesgo real de concurrencia;
- validadores reutilizables;
- claves foráneas protegidas apropiadamente;
- bajas lógicas o estados inactivos en catálogos cuando borrar rompería historia;
- timestamps de creación y modificación;
- servicios para reglas de negocio complejas.

No guardes “totales” duplicados si pueden calcularse con consultas confiables, salvo que sea un snapshot histórico intencional y documentado.

## 17. Seguridad y privacidad

Se trabaja con expedientes de empleados.

Implementa desde el inicio:

- autenticación obligatoria;
- autorización por permisos;
- protección CSRF;
- sesiones seguras configurables;
- no exponer rutas absolutas de servidor innecesariamente;
- no registrar datos sensibles completos en logs de aplicación;
- validación estricta de archivos importados;
- límites de tamaño configurables;
- auditoría de descargas/exportaciones si se implementan;
- principio de mínimo privilegio.

No uses servicios externos de IA/OCR con documentos reales sin una decisión institucional explícita sobre privacidad, contrato y tratamiento de datos.

## 18. Experiencia de usuario

La interfaz debe estar pensada para un digitalizador que necesita trabajar rápido y reducir errores.

Aplicar:

- lenguaje claro en español;
- botones con verbos concretos;
- estados visibles;
- siguiente acción evidente;
- filtros persistentes cuando ayuden;
- validaciones cerca del campo;
- confirmación para acciones críticas;
- no pedir dos veces un dato que el sistema ya conoce;
- evitar modales innecesarios;
- colores no deben ser la única forma de transmitir estado;
- tablas legibles;
- accesibilidad básica;
- mensajes de error que expliquen cómo corregir.

## 19. Arquitectura sugerida de apps Django

Si el repositorio está vacío, una estructura inicial razonable es:

```text
config/
apps/
  core/
  accounts/
  people/
  sources/
  batches/
  records/
  digitization/
  quality/
  reports/
templates/
static/
docs/
tests/
```

No es obligatorio respetarla si otra estructura resulta mejor, pero explica cualquier cambio importante.

Mantén:

- modelos delgados cuando la lógica sea de proceso;
- servicios de dominio para transiciones y conciliaciones;
- selectors/query services para consultas complejas si ayudan;
- forms para validación de entrada;
- vistas simples;
- templates sin lógica de negocio.

## 20. Datos iniciales y configuración

Crea comandos idempotentes o migraciones de datos para:

- grupos/roles;
- permisos custom;
- sistemas Federal/Estatal;
- tipos documentales iniciales DP/FP/HL;
- configuración mínima.

No crees usuarios reales ni contraseñas por defecto dentro del repositorio.

Permite crear un superusuario mediante instrucciones en README.

## 21. Pruebas obligatorias del primer MVP

Como mínimo cubre pruebas de:

### CURP

- normalización;
- longitud;
- duplicados relevantes.

### Sistemas

- persona Federal;
- Estatal;
- ambos.

### Roles

- digitalizador no accede a expediente ajeno;
- supervisor puede asignar;
- revisor puede observar/validar;
- consulta no modifica.

### Estados

- transiciones válidas;
- transiciones inválidas;
- cierre por digitalizador ≠ validación;
- observación y corrección preservan historia.

### Conteos

- físicos separados de digitales;
- `individual + multi = total digital` cuando el resumen está completo;
- multi no depende de page count.

### BAT/CSV

- importación válida;
- importación duplicada;
- discrepancia de cantidades;
- fila inválida;
- CURP inexistente.

### Catálogos

- desactivar tipo no destruye registros históricos.

### Auditoría

- acciones críticas generan evento.

### Excel

- archivo válido de prueba;
- filas con errores;
- duplicados;
- conciliación.

Usa fixtures/factories de datos sintéticos. No incluyas información real de empleados en tests.

## 22. Documentación obligatoria

Crear o actualizar:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/DOMAIN_MODEL.md`
- `docs/WORKFLOW.md`
- `docs/PERMISSIONS.md`
- `docs/IMPORT_EXCEL.md`
- `docs/BAT_INTEGRATION.md`
- `docs/OPEN_QUESTIONS.md`
- `docs/IMPLEMENTATION_PLAN.md`
- `.env.example`

El README debe explicar para un principiante:

1. qué problema resuelve el sistema;
2. cómo instalar Python/crear venv si hace falta;
3. cómo instalar dependencias;
4. cómo aplicar migraciones;
5. cómo crear superusuario;
6. cómo cargar datos iniciales;
7. cómo ejecutar tests;
8. cómo arrancar servidor local;
9. dónde cambiar configuración.

## 23. Fases de implementación

No intentes resolver OCR/IA, movimiento automático y toda la reportería avanzada en una sola pasada.

### Fase 0 — Fundaciones

- inspección del repositorio;
- proyecto Django;
- configuración;
- apps base;
- autenticación;
- roles/permisos;
- layout de interfaz;
- documentación.

### Fase 1 — Flujo operativo MVP

- personas/fuente oficial;
- lotes;
- importación Excel;
- expedientes;
- asignación;
- conteo físico;
- incidencias;
- cierre por digitalizador;
- revisión/observación/validación;
- auditoría.

### Fase 2 — Digitalización y conciliación

- documentos lógicos;
- modalidades de escaneo;
- inventario TIFF;
- importación de resumen BAT;
- conteos automáticos;
- conciliación;
- reportes operativos.

### Fase 3 — Sustitución progresiva del BAT

- previsualización de organización;
- reglas configurables;
- movimiento/renombrado controlado;
- rollback lógico/auditoría;
- procesamiento de lotes.

### Fase 4 — OCR y clasificación asistida

- OCR local/institucional autorizado;
- extracción de señales;
- clasificación sugerida;
- confidence score;
- confirmación humana;
- métricas de precisión;
- versionado de modelos.

En esta ejecución debes llegar como mínimo a una **Fase 1 funcional y probada**, y dejar preparada la estructura de Fase 2. Si el tamaño del repositorio o un sistema existente obliga a avanzar de manera distinta, documenta el motivo y prioriza integridad sobre cantidad de funciones.

## 24. Criterios de aceptación del MVP

El trabajo se considera correctamente iniciado cuando:

1. El proyecto arranca en el entorno local documentado.
2. Las migraciones aplican desde una base limpia.
3. Existe autenticación.
4. Los grupos/permisos iniciales se cargan idempotentemente.
5. Puede crearse un lote.
6. Puede importarse un Excel de prueba mediante mapeo definido.
7. Puede registrarse/conciliar un expediente.
8. Un supervisor puede asignarlo a un digitalizador.
9. El digitalizador ve únicamente lo autorizado.
10. Puede registrar hojas físicas sin confundirlas con archivos TIFF.
11. Puede registrar incidencias desde catálogo.
12. Puede terminar su trabajo enviándolo a revisión.
13. El responsable puede observar o validar.
14. Las acciones críticas dejan historial.
15. Existe una base para registrar INDIVIDUAL/MULTI y TIFF sin inferir modalidad por páginas.
16. Las reglas DP/FP/HL son configurables desde catálogo/datos semilla.
17. Existe adaptador inicial para importar el CSV del BAT o, si se deja para Fase 2, la interfaz y tests de contrato quedan preparados y documentados.
18. Los tests principales pasan.
19. No hay secretos ni datos reales dentro del repositorio.
20. La documentación explica claramente cómo usar y continuar el sistema.

## 25. Reglas de calidad de implementación

- No desactives tests para conseguir “verde”.
- No ocultes excepciones con `except Exception: pass`.
- No hagas migraciones destructivas sin necesidad.
- No uses datos falsos como si fueran reglas oficiales.
- No hardcodees IDs de usuarios, grupos o catálogos.
- No dupliques reglas de transición en varias vistas.
- No implementes permisos solamente ocultando botones: valida también en backend.
- No cambies automáticamente datos importados sin dejar rastro.
- No confíes en el nombre del TIFF como única evidencia futura; registra metadatos y clasificación confirmada.
- No borres archivos TIFF por una detección de “blanco”.
- No uses CURP real ni documentos reales en pruebas o screenshots.

## 26. Entregable al finalizar tu trabajo

Cuando termines la implementación, responde con un informe estructurado que incluya:

1. **Diagnóstico inicial del repositorio**.
2. **Arquitectura implementada**.
3. **Modelos y reglas de negocio**.
4. **Roles y permisos**.
5. **Flujo funcional disponible**.
6. **Importación y conciliaciones**.
7. **Auditoría**.
8. **Pruebas ejecutadas**, indicando comando y resultado.
9. **Migraciones creadas**.
10. **Archivos principales modificados**, con ruta.
11. **Decisiones importantes y por qué se tomaron**.
12. **Preguntas abiertas que requieren contexto real del área**.
13. **Riesgos conocidos**.
14. **Siguiente incremento recomendado**.
15. **Instrucciones exactas para que un principiante ejecute el sistema en macOS 11.7.11**.

Si algo no puede implementarse de forma correcta porque falta una regla real del proceso, no inventes la regla. Implementa la estructura configurable, deja el punto claramente marcado en `docs/OPEN_QUESTIONS.md` y continúa con el resto de forma segura.

El objetivo es construir un sistema que ayude a que el proceso sea **más rápido, verificable y trazable**, sin sacrificar el control humano necesario sobre expedientes oficiales.
