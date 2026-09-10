# Importación de Excel oficial

## Alcance

El adaptador actual admite `.xlsx`. No admite `.xls`, macros ni archivos externos. La fuente de Nóminas se conserva con nombre original, usuario, fecha, SHA-256, mapeo, totales y cada fila original.

## Mapeo

En el lote, el responsable indica:

- hoja y número de fila de encabezados;
- encabezado CURP obligatorio;
- encabezados opcionales de nombre y estado;
- una columna combinada de sistema o columnas separadas Federal/Estatal;
- listas explícitas de valores que significan Federal, Estatal, Activo e Inactivo.

Los textos deben coincidir con el encabezado real. No existen alias ocultos ni nombres de columna inventados. Los valores se comparan sin distinguir mayúsculas/minúsculas; una columna combinada puede separar valores con coma, punto y coma, diagonal, barra o `+`.

## Validaciones

- extensión y tamaño máximo configurado;
- estructura legible `.xlsx`;
- hoja/fila/encabezados existentes;
- hash ya importado;
- CURP vacía o formato evidentemente inválido;
- fila exacta duplicada y CURP duplicada dentro del archivo;
- valor de sistema no reconocido por el mapeo.

Una fila con error se conserva pero no crea/actualiza persona. Una fila aceptada crea la persona o actualiza su vista actual; cualquier cambio de nombre/estado genera auditoría y el snapshot anterior permanece intacto.

## Conciliación

Después de importar:

1. se asocia una fuente oficial al lote; una importación ya existente puede reutilizarse en otro lote sin duplicar el archivo;
2. **Crear expedientes desde Excel** materializa filas aceptadas de forma idempotente;
3. el panel compara esperados, registrados, filas sin expediente y expedientes sin fila;
4. un expediente físico sin fila puede registrarse por separado para que la diferencia sea explícita.

Antes de usar un archivo real, confirme las preguntas de esquema y semántica en `OPEN_QUESTIONS.md`.
