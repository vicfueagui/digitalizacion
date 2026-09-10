# Integración con el BAT v2

## Archivos admitidos

Desde la ficha de un lote puede importarse `RESUMEN_DIGITALIZACION.csv` o `CONTROL_DIGITALIZACION.csv` generado por `organizar_tiff_por_curp_v2.bat`. El delimitador esperado es punto y coma y la codificación puede ser UTF-8 o Windows-1252.

Las columnas obligatorias son:

```text
CURP;FISICOS;DIGITALES;INDIVIDUALES;MULTI;RESULTADO
```

Las columnas adicionales del BAT se conservan en `raw_payload`.

## Controles

- hash de archivo ya importado;
- formato básico de CURP;
- existencia de la CURP dentro del lote elegido;
- enteros no negativos y `NO_CAPTURADO` para físicos;
- `INDIVIDUALES + MULTI = DIGITALES`;
- fila exacta ya importada previamente para el lote;
- diferencia con el último conteo físico;
- diferencia con el inventario TIFF cuando ya existe.

Cada fila queda como aceptada, con discrepancias, con error o duplicada. La fila original, errores y discrepancias quedan almacenados. La importación no crea una validación ni cambia el estado del expediente.

## Inventario TIFF

La ficha de expediente permite verificar una carpeta bajo `DIGITAL_REPOSITORY_ROOT`. Por defecto busca la subcarpeta con la CURP y:

- encuentra `.tif`/`.tiff` recursivamente;
- cuenta prefijos y carpetas;
- comprueba DP/FP → `PERSONALES` y HL → `FEDERAL` usando `DocumentType`;
- registra tamaño y, opcionalmente, SHA-256;
- marca metadatos no encontrados en la siguiente verificación sin borrarlos.

La operación es read/verify: no mueve, renombra, sobrescribe ni elimina ningún TIFF. `SCANNER_INBOX_ROOT` también está abstraído para una fase posterior.
