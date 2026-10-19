CREATE TABLE procedencia_paginas(
 archivo_id INTEGER NOT NULL REFERENCES archivos_tiff(id),
 pagina INTEGER NOT NULL CHECK(pagina>0),
 archivo_fuente_id INTEGER NOT NULL REFERENCES archivos_tiff(id),
 version_fuente_id TEXT NOT NULL REFERENCES versiones_archivo(id),
 pagina_fuente INTEGER NOT NULL CHECK(pagina_fuente>0),
 operacion_id INTEGER NOT NULL REFERENCES operaciones_tiff(id),
 PRIMARY KEY(archivo_id,pagina)
);
CREATE INDEX idx_procedencia_fuente ON procedencia_paginas(archivo_fuente_id,version_fuente_id);
CREATE TRIGGER procedencia_inmutable BEFORE UPDATE ON procedencia_paginas
BEGIN SELECT RAISE(ABORT,'La procedencia documental es inmutable.'); END;
CREATE TRIGGER procedencia_no_borrar BEFORE DELETE ON procedencia_paginas
BEGIN SELECT RAISE(ABORT,'La procedencia documental se conserva.'); END;
