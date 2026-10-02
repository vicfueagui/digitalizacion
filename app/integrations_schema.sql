CREATE TABLE integraciones(
 id INTEGER PRIMARY KEY,
 trabajo_id INTEGER NOT NULL REFERENCES trabajos(id),
 numero INTEGER NOT NULL CHECK(numero>=0),
 folio_id INTEGER NOT NULL REFERENCES folios(id),
 prestamo_item_id INTEGER REFERENCES prestamo_items(id),
 referencia TEXT NOT NULL DEFAULT '',
 motivo TEXT NOT NULL,
 recibido TEXT,
 fisicos INTEGER CHECK(fisicos>=0),
 estado TEXT NOT NULL,
 digitalizador TEXT NOT NULL DEFAULT '',
 creado TEXT NOT NULL,
 cerrado TEXT,
 operador TEXT NOT NULL,
 origen TEXT NOT NULL,
 UNIQUE(trabajo_id,numero)
);
ALTER TABLE trabajos ADD COLUMN integracion_actual_id INTEGER REFERENCES integraciones(id);
ALTER TABLE conteos ADD COLUMN integracion_id INTEGER REFERENCES integraciones(id);
ALTER TABLE archivos_tiff ADD COLUMN integracion_id INTEGER REFERENCES integraciones(id);
ALTER TABLE archivos_tiff ADD COLUMN integracion_ingreso_id INTEGER REFERENCES integraciones(id);
ALTER TABLE historial ADD COLUMN integracion_id INTEGER REFERENCES integraciones(id);
CREATE INDEX idx_integraciones_trabajo ON integraciones(trabajo_id,numero);
CREATE INDEX idx_conteos_integracion ON conteos(integracion_id,activo);
CREATE INDEX idx_archivos_integracion ON archivos_tiff(integracion_id,activo);
CREATE TABLE lotes_tiff(
 id TEXT PRIMARY KEY,trabajo_id INTEGER NOT NULL REFERENCES trabajos(id),accion TEXT NOT NULL,
 motivo TEXT NOT NULL,operador TEXT NOT NULL,creado TEXT NOT NULL,estado TEXT NOT NULL,
 seleccion TEXT NOT NULL,resultado TEXT NOT NULL DEFAULT '{}'
);
CREATE TRIGGER integracion_inicial AFTER INSERT ON trabajos BEGIN
 INSERT INTO integraciones(trabajo_id,numero,folio_id,prestamo_item_id,motivo,recibido,fisicos,estado,digitalizador,creado,operador,origen)
 VALUES(NEW.id,0,NEW.folio_id,NEW.prestamo_item_id,'Carga inicial',NEW.recibido,NEW.fisicos,NEW.estado,NEW.digitalizador,NEW.estado_desde,'','Alta del ciclo');
 UPDATE trabajos SET integracion_actual_id=(SELECT id FROM integraciones WHERE trabajo_id=NEW.id AND numero=0) WHERE id=NEW.id;
END;
CREATE TRIGGER integracion_contexto AFTER UPDATE OF prestamo_item_id,recibido,digitalizador ON trabajos BEGIN
 UPDATE integraciones SET prestamo_item_id=COALESCE(prestamo_item_id,NEW.prestamo_item_id),
 recibido=CASE WHEN numero=0 THEN NEW.recibido ELSE recibido END,digitalizador=NEW.digitalizador
 WHERE id=NEW.integracion_actual_id;
END;
CREATE TRIGGER integracion_estado AFTER UPDATE OF estado ON trabajos BEGIN
 UPDATE integraciones SET estado=NEW.estado,
 cerrado=CASE WHEN NEW.estado='Expediente cerrado' THEN COALESCE(cerrado,NEW.estado_desde) ELSE NULL END
 WHERE id=NEW.integracion_actual_id;
END;
CREATE TRIGGER conteo_integracion AFTER INSERT ON conteos WHEN NEW.integracion_id IS NULL BEGIN
 UPDATE conteos SET integracion_id=(SELECT integracion_actual_id FROM trabajos WHERE id=NEW.trabajo_id) WHERE id=NEW.id;
END;
CREATE TRIGGER tiff_integracion AFTER INSERT ON archivos_tiff WHEN NEW.integracion_id IS NULL OR NEW.integracion_ingreso_id IS NULL BEGIN
 UPDATE archivos_tiff SET integracion_id=COALESCE(NEW.integracion_id,(SELECT integracion_actual_id FROM trabajos WHERE id=NEW.trabajo_id)),
 integracion_ingreso_id=COALESCE(NEW.integracion_ingreso_id,(SELECT integracion_actual_id FROM trabajos WHERE id=NEW.trabajo_id)) WHERE id=NEW.id;
END;
CREATE TRIGGER historial_integracion AFTER INSERT ON historial WHEN NEW.integracion_id IS NULL BEGIN
 UPDATE historial SET integracion_id=(SELECT integracion_actual_id FROM trabajos WHERE id=NEW.trabajo_id) WHERE id=NEW.id;
END;
CREATE TRIGGER integracion_actual_mismo_trabajo BEFORE UPDATE OF integracion_actual_id ON trabajos
 WHEN NEW.integracion_actual_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_actual_id AND trabajo_id=NEW.id)
 BEGIN SELECT RAISE(ABORT,'La integracion pertenece a otro expediente'); END;
CREATE TRIGGER conteo_integracion_mismo_trabajo BEFORE UPDATE OF integracion_id ON conteos
 WHEN NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_id AND trabajo_id=NEW.trabajo_id)
 BEGIN SELECT RAISE(ABORT,'El conteo pertenece a otra integracion'); END;
CREATE TRIGGER archivo_integracion_mismo_trabajo BEFORE UPDATE OF integracion_id,integracion_ingreso_id ON archivos_tiff
 WHEN NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_id AND trabajo_id=NEW.trabajo_id)
 OR NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_ingreso_id AND trabajo_id=NEW.trabajo_id)
 BEGIN SELECT RAISE(ABORT,'El TIFF pertenece a otra integracion'); END;
CREATE TRIGGER conteo_insertar_integracion BEFORE INSERT ON conteos
 WHEN NEW.integracion_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_id AND trabajo_id=NEW.trabajo_id)
 BEGIN SELECT RAISE(ABORT,'El conteo pertenece a otra integracion'); END;
CREATE TRIGGER archivo_insertar_integracion BEFORE INSERT ON archivos_tiff
 WHEN (NEW.integracion_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_id AND trabajo_id=NEW.trabajo_id))
 OR (NEW.integracion_ingreso_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM integraciones WHERE id=NEW.integracion_ingreso_id AND trabajo_id=NEW.trabajo_id))
 BEGIN SELECT RAISE(ABORT,'El TIFF pertenece a otra integracion'); END;
