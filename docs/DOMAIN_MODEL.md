# Modelo de dominio

## Separación conceptual

| Concepto | Modelo/campo | Regla |
|---|---|---|
| Hoja física | `PhysicalCount.sheet_count` | Registro versionado; un reconteo no reemplaza al anterior. |
| Documento lógico | `DigitalDocument` | Tiene tipo confirmado y modalidad operativa. |
| Archivo TIFF | `DigitalAsset` | Un registro por ruta relativa, con tamaño/hash/estado. |
| Página digital | `DigitalPage` y `DigitalAsset.page_count` | Registro individual opcional y metadato nullable, ambos independientes de modalidad. |

Nunca se deriva `scan_mode` de `page_count`.

## Relaciones principales

```text
PayrollImport 1 --- n PayrollSourceRow --- 0..1 Person

Person n --- n AdministrativeSystem
  |
  1
  |
  n PersonnelRecord n --- 1 IntakeBatch
       |       |       |
       |       |       +--- n RecordAssignment
       |       +----------- n PhysicalCount / Incident / QualityReview
       +------------------- n DigitalDocument --- n DigitalAsset
                              |
                              +--- ScanMode y DocumentType configurables
```

## Datos oficiales

`PayrollImport` representa el archivo completo. `PayrollSourceRow` conserva la fila, CURP original/normalizada, resultado, errores, advertencias, sistemas detectados con el mapeo y relación a persona. Una importación nueva no elimina snapshots anteriores.

`Person` es la identidad operativa actual. Su llave técnica es numérica y la CURP es una llave de negocio única. `PersonSystemMembership` permite Federal, Estatal o ambas; la fila oficial sigue siendo el snapshot que explica de dónde vino la información.

## Expediente y trazabilidad

`PersonnelRecord` existe dentro de un lote. Conserva su fuente, sistema esperado, sistemas declarados, identificador físico, estado y custodio actual. `RecordAssignment` conserva todas las asignaciones; solo una puede estar activa por constraint.

`RecordStatusTransition`, `PhysicalCount` y `QualityReview` son históricos. La interfaz administrativa no permite editarlos o borrarlos. `AuditEvent` agrega actor, acción, entidad, antes/después y contexto.

## Catálogos

- `AdministrativeSystem`: se inicializan `FEDERAL` y `ESTATAL`.
- `DocumentType`: se inicializan DP/FP → `PERSONALES` y HL → `FEDERAL`. Sus significados completos siguen pendientes.
- `IncidentType`: no recibe datos inventados; el administrador funcional carga el catálogo aprobado.

Los catálogos se desactivan; no se borran si ya tienen historia.

## Importación de transición

`BatCsvImport` y `BatCsvRow` son snapshots externos. Separan físicos, digitales, individuales y multi, conservan discrepancias y nunca cambian el estado a validado.
