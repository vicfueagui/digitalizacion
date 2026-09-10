# Preguntas abiertas

Estas preguntas requieren confirmación del área. El sistema no tratará las respuestas provisionales como reglas oficiales.

## Datos oficiales e importación

1. ¿Cuáles son los encabezados, tipos de dato, hojas y variantes reales del Excel de Nóminas?
2. ¿Cómo representa el Excel el estado activo/inactivo y la pertenencia Federal, Estatal o ambas?
3. ¿Qué columnas, además de CURP, deben conservarse y mostrarse como datos oficiales?
4. ¿Una misma persona puede aparecer más de una vez en un archivo por plazas, sistemas u otra causa válida?
5. ¿Qué autoridad y regla institucional deben usarse para validar la estructura completa y el dígito verificador de una CURP? Mientras se confirma, se aplicará solamente la validación evidente documentada: 18 caracteres alfanuméricos, normalizados a mayúsculas y sin espacios (como hace el BAT v2).

El importador usará un mapeo explícito por archivo y conservará cada fila original. No asumirá encabezados desconocidos.

## Expedientes, lotes y custodia

6. ¿Cómo se genera el identificador oficial de un lote y qué estados/cancelaciones usa el área?
7. ¿Existe un identificador físico del folder distinto de la CURP y cuál es su formato?
8. ¿Cuáles son las ubicaciones físicas y estaciones de trabajo autorizadas que deben formar catálogos?
9. ¿Cómo se registra la lista de expedientes físicos recibidos antes de conciliarla con Excel?
10. ¿Qué motivos y autorizaciones se requieren para cancelar un expediente o lote?

Los identificadores y ubicaciones quedan como campos configurables/de texto controlado hasta recibir catálogos oficiales. Las cancelaciones requieren permiso y motivo, pero no se automatizará su política.

## Clasificación e incidencias

11. ¿Cuál es el nombre y significado documental completo de DP, FP y HL?
12. ¿Cuál es el catálogo aprobado de incidencias, sus categorías, severidades, bloqueos y vigencias?
13. ¿Hay otros prefijos, carpetas destino o reglas de aplicabilidad además de DP/FP → `PERSONALES` y HL → `FEDERAL`?
14. ¿La palabra `PERSONALES` en la estructura de carpetas tiene alguna relación con el sistema administrativo Estatal? Las fuentes solamente confirman que es un destino de DP/FP; el sistema no inferirá otra relación.

Se sembrarán solamente los códigos y destinos confirmados. Los nombres semánticos quedarán iguales al código hasta que el área los defina. No se sembrarán incidencias provisionales.

## Revisión y operación

15. ¿Un usuario que pertenece simultáneamente a Digitalizadores y Revisores puede validar trabajo propio? El MVP aplicará separación estricta y lo impedirá.
16. ¿Qué incidencias bloquean el envío a revisión y cuáles bloquean la validación?
17. ¿Qué conteos y evidencias son obligatorios para enviar, validar y cerrar definitivamente?
18. ¿Quién ejecuta el cierre final después de `VALIDATED` y qué comprobación adicional requiere?
19. ¿Se permite reasignar un expediente que ya está en proceso y qué entrega física lo acompaña?

El MVP preservará todas las transiciones, observaciones y reasignaciones. No cerrará ni validará automáticamente.

## Infraestructura, privacidad y conservación

20. ¿Cuáles serán las rutas de red autorizadas para entrada del escáner y repositorio digital?
21. ¿Qué límites de tamaño, antivirus y cuarentena se aplicarán a archivos Excel/CSV?
22. ¿Cuánto tiempo deben conservarse archivos fuente, bitácoras, sesiones y metadatos?
23. ¿Qué campos personales pueden mostrarse a cada rol y qué política institucional aplica a respaldos, exportaciones y logs?
24. ¿La instalación productiva usará proxy TLS, SSO/directorio institucional y PostgreSQL administrado?
25. ¿La firma de recepción de lote y expedientes seguirá siendo física o requiere firma electrónica/evidencia adjunta? El MVP registra actor, fecha y confirmación, pero no inventa un mecanismo de firma.

La configuración se expondrá por variables de entorno. No habrá integración externa, OCR ni movimiento de archivos hasta contar con autorización y controles operativos.
