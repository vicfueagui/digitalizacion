CREATE TABLE documentos_logicos(id TEXT PRIMARY KEY,expediente_id TEXT NOT NULL REFERENCES expedientes(id),secuencia INTEGER NOT NULL,nombre_origen TEXT,creado TEXT NOT NULL,estado TEXT NOT NULL DEFAULT 'Activo',UNIQUE(expediente_id,secuencia));
CREATE TABLE versiones_archivo(id TEXT PRIMARY KEY,documento_id TEXT NOT NULL REFERENCES documentos_logicos(id),anterior_id TEXT REFERENCES versiones_archivo(id),ruta TEXT NOT NULL,sha256 TEXT NOT NULL,bytes INTEGER,paginas INTEGER,creado TEXT NOT NULL,operador TEXT NOT NULL,accion TEXT NOT NULL,estado TEXT NOT NULL,archivo_origen_id INTEGER REFERENCES archivos_tiff(id));
ALTER TABLE archivos_tiff ADD COLUMN documento_id TEXT REFERENCES documentos_logicos(id);
ALTER TABLE archivos_tiff ADD COLUMN version_id TEXT REFERENCES versiones_archivo(id);
ALTER TABLE archivos_tiff ADD COLUMN nombre_origen TEXT;
CREATE INDEX idx_version_documento ON versiones_archivo(documento_id);
CREATE TRIGGER version_contenido_inmutable BEFORE UPDATE OF id,documento_id,sha256,paginas ON versiones_archivo
BEGIN SELECT RAISE(ABORT,'La identidad y contenido de una versión son inmutables.'); END;
