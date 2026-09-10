# Contexto funcional inicial — Sistema de Digitalización de Expedientes SEGEY

Fecha de consolidación: 06/09/2026

## 1. Propósito

Diseñar un sistema profesional, intuitivo y auditable para apoyar el proceso de digitalización de expedientes de personal del Archivo General de la Secretaría de Educación del Estado de Yucatán (SEGEY).

El sistema debe reducir errores, capturas duplicadas, conteos manuales, pérdida de trazabilidad y validaciones repetitivas, sin eliminar decisiones humanas que todavía requieren criterio documental.

## 2. Origen de la información

El área de Nóminas maneja información oficial del empleado. Archivo General utiliza esa información como referencia para organizar y digitalizar expedientes.

Los empleados pueden presentar distintas condiciones:

- activos o inactivos en nómina;
- pertenecientes al sistema Federal;
- pertenecientes al sistema Estatal;
- pertenecientes a ambos sistemas.

La pertenencia a Federal y Estatal NO debe modelarse como un único campo excluyente.

## 3. Alcance operativo actual

El área de digitalización descrita trabaja por el momento con expedientes/documentación Federal. Existe riesgo frecuente de que dentro de un expediente Federal haya documentación Estatal o documentación de otra persona.

El sistema debe permitir registrar y posteriormente reportar estas incidencias.

## 4. Recepción y lotes

El expediente físico llega a Archivo General, donde previamente puede ser organizado, integrado a un folder y etiquetado.

Al responsable de digitalización se le entrega un conjunto/lote de expedientes físicos y un archivo Excel con información digital que debe corresponder a esos expedientes.

El responsable firma de recibido y queda a cargo de distribuir expedientes entre digitalizadores.

Se necesita trazabilidad desde la recepción del lote hasta el cierre/validación.

## 5. Asignación a digitalizador

El responsable asigna determinados expedientes a un digitalizador.

El digitalizador recibe:

- expedientes físicos;
- la información digital correspondiente, actualmente mediante Excel.

Antes de iniciar debe validar que el expediente físico y la información digital correspondan.

## 6. Conteo físico

El digitalizador toma un expediente y cuenta todas sus hojas físicas.

Durante este conteo puede detectar, entre otras situaciones:

- expediente mal organizado;
- hojas fuera del broche del folder;
- documentación Estatal dentro de un expediente Federal;
- documentación de otra persona;
- otras incidencias que deberán formar parte de un catálogo estandarizado.

El conteo se anota actualmente en el folder físico, por ejemplo:

`Fisicos 156, Fecha 04/09/2026, Digitalizador ...`

El mismo dato debe quedar registrado digitalmente.

## 7. Digitalización

Después del conteo se escanean todas las hojas que correspondan al expediente, independientemente de tamaño, visibilidad, grosor, antigüedad o condición.

Existen riesgos de operación con:

- hojas rotas;
- hojas dobladas;
- papel cebolla;
- hojas antiguas;
- hojas recicladas o con información previa marcada/rayada;
- documentos de diferentes tamaños.

El digitalizador debe validar visualmente la calidad del resultado y ajustar el tono cuando sea necesario.

## 8. Conceptos que NO deben mezclarse

El sistema debe separar explícitamente:

### Hojas físicas

Piezas reales de papel del expediente.

### Páginas digitales

Caras/páginas contenidas dentro de uno o más TIFF.

### Archivos digitales TIFF

Cantidad de archivos `.tif` o `.tiff` que conforman el expediente digital organizado.

Una hoja física puede generar más de una página digital. Un TIFF puede contener una o varias páginas.

## 9. Modalidades de escaneo conocidas

### INDIVIDUAL UNA CARA

Cada hoja/documento individual produce un TIFF independiente de una página.

Ejemplo: 5 hojas procesadas → 5 TIFF.

### METLIFE / individual a doble cara

Puede procesar varias hojas a doble cara y generar un TIFF por hoja, donde cada TIFF contiene dos páginas.

Ejemplo: 5 hojas a doble cara → 5 TIFF, cada TIFF con dos páginas.

Por lo tanto:

**TIFF con más de una página NO implica automáticamente MULTI.**

### MULTI UNA CARA

Varias hojas físicas que pertenecen a un mismo documento se agrupan en un solo TIFF multipágina.

Si dentro del documento una hoja necesita incluir una segunda cara, esa cara también se incorpora al mismo TIFF. Por tanto, el número de páginas del TIFF puede ser mayor que el número de hojas físicas del documento.

## 10. Clasificación documental actual

Por el momento el proceso utiliza al menos los códigos/prefijos:

- `DP-`
- `FP-`
- `HL-`

El BAT existente aplica las reglas:

- `DP-` y `FP-` → carpeta `PERSONALES`
- `HL-` → carpeta `FEDERAL`

Estas reglas deben tratarse como catálogo/configuración de negocio y no quedar dispersas en múltiples partes del futuro sistema.

La definición semántica completa de todos los tipos documentales debe poder crecer sin modificar código cada vez que aparezca un nuevo tipo.

## 11. Organización por CURP

Actualmente el BAT solicita una CURP y crea:

```text
CURP\
├── PERSONALES\
└── FEDERAL\
```

Los TIFF se mueven según prefijo.

La CURP funciona como identificador operativo principal del expediente, pero el modelo de datos debe permitir identificadores internos propios y no usar la CURP como única llave técnica de todas las tablas.

## 12. Registro al terminar el escaneo

Actualmente se registra en el folder físico una anotación como:

`Digitales 9, Fecha 05/09/2026, Digitalizador: Victor`

También se registra en Excel:

- físicos;
- digitales;
- incidencias;
- otros datos de control.

Se requiere agregar y reportar al menos:

- total de digitales TIFF;
- cantidad INDIVIDUAL;
- cantidad MULTI.

El sistema debe poder derivar automáticamente los conteos que realmente se puedan obtener del almacenamiento y pedir confirmación humana para lo que dependa de la modalidad de trabajo.

## 13. Cierre por digitalizador

Al terminar:

- se reorganiza el expediente físico como estaba al inicio;
- se cierra físicamente;
- el digitalizador registra que concluyó su trabajo;
- la información debe quedar disponible para el responsable.

Para evitar ambigüedad, el sistema debe diferenciar entre:

- terminado por digitalizador / pendiente de validación;
- validado por responsable;
- observado para corrección;
- cerrado finalmente.

## 14. Validación del responsable

El responsable puede revisar:

- conteo físico;
- anotaciones del folder;
- fechas;
- datos capturados;
- estructura de la carpeta CURP;
- cantidad de digitales;
- correspondencia entre archivos y datos registrados;
- incidencias;
- trabajo del digitalizador.

Actualmente parte de esta validación se hace contando manualmente los TIFF de cada CURP y haciendo sumatorias para compararlas con Excel.

El sistema debe automatizar estas conciliaciones cuando sea posible y resaltar diferencias.

## 15. Incidencias

Se está creando un catálogo de incidencias.

El sistema debe implementar un catálogo administrable con:

- código;
- nombre;
- descripción;
- categoría;
- severidad/prioridad;
- si bloquea o no el avance;
- activo/inactivo;
- vigencia;
- evidencia/notas asociadas a cada incidencia real.

No se debe hardcodear un catálogo provisional dentro de la lógica.

## 16. Trazabilidad y custodia

Debe quedar registro auditable de:

- recepción del lote;
- asignación de expediente;
- recepción por digitalizador;
- inicio y fin de trabajo;
- conteos físicos;
- archivos digitales detectados;
- cambios de estatus;
- incidencias;
- correcciones;
- validación/rechazo;
- usuario, fecha y hora de cada acción relevante.

Los registros históricos no deben sobrescribirse silenciosamente.

## 17. Clasificación automática futura

Objetivo futuro: analizar el contenido de TIFF y sugerir qué tipo documental corresponde.

Debe diseñarse como sistema asistido:

1. OCR/análisis de imagen opcional;
2. clasificador genera tipo sugerido;
3. devuelve nivel de confianza;
4. usuario confirma o corrige;
5. la confirmación humana queda auditada;
6. los datos confirmados pueden alimentar mejoras futuras del clasificador.

En etapas iniciales NO se debe renombrar o clasificar automáticamente de manera irreversible basándose solamente en una predicción.

## 18. Hojas recicladas y páginas aparentemente irrelevantes

No se debe implementar una regla simple de “página en blanco = eliminar”.

En los expedientes pueden existir:

- reversos con información antigua;
- texto rayado;
- marcas a lápiz o pluma;
- información reutilizada;
- páginas de baja visibilidad.

Cualquier detección automática de página vacía debe ser solamente una sugerencia de revisión, nunca una eliminación automática en la etapa inicial.

## 19. Roles iniciales sugeridos

### Administrador

Configuración global, usuarios, permisos, catálogos y administración técnica/funcional.

### Responsable de digitalización / Supervisor

Recibe lotes, importa Excel, distribuye expedientes, consulta productividad, revisa diferencias, valida u observa trabajos.

### Digitalizador

Trabaja únicamente los expedientes asignados, registra conteos, incidencias, modalidad, avances y cierre de su trabajo.

### Revisor / Control de calidad

Puede revisar expedientes terminados, registrar observaciones y validar controles de calidad sin tener permisos administrativos generales.

### Consulta / Auditoría

Lectura de expedientes, historial, reportes y bitácoras, sin modificar operación.

Los permisos deben implementarse por capacidades/grupos, no mediante condicionales dispersos por nombre de usuario.

## 20. Principios del sistema

- fuente oficial identificable;
- trazabilidad de punta a punta;
- mínima captura duplicada;
- validaciones automáticas antes que sumas manuales;
- intervención humana explícita en decisiones documentales;
- catálogos configurables;
- historial inmutable de acciones relevantes;
- interfaz clara para usuarios no técnicos;
- no destruir ni sobrescribir evidencia sin una acción explícita y auditada;
- separar el expediente físico, el documento lógico, el archivo TIFF y la página digital como conceptos diferentes.
