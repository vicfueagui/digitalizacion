# Operación del modelo 0.5.0

**Antecedente de la versión 0.5.0.** Para los botones actuales y el recorrido completo de 0.6.2 consulta el [Manual de uso](MANUAL_USUARIO.html). Esta página conserva la explicación del modelo; las ampliaciones posteriores están integradas en el manual vigente.

Para practicar en este Mac:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python main.py --workspace ensayos/modelo-operativo-v05/demo
```

Es una demo ficticia con tres maestros, dos legajos de la misma identidad, recepción/asignación, entregas v1/v2, una observación respondida pendiente de validar y un reescaneo pendiente. No se usa como base de producción. Para empezar de nuevo, `main.py --crear-demo demos/NOMBRE_NUEVO` exige una carpeta inexistente.

## Recepción y asignación

1. En **Folios**, crea el folio y abre **Recepción / préstamo**. En la interfaz actual, **Más acciones → Registrar entrega / recepción del folio** guarda área, entrega/recibe y referencia de acuse. Una fecha vacía registra la recepción actual; no la uses para inventar fechas históricas.
2. Añade cada expediente esperado con CURP, legajo y ubicación original. En la interfaz actual, **Aceptar seleccionados** confirma los físicos cotejados sin recapturar CURP; **Revisar diferencia** registra faltante, discrepancia o pendiente con evidencia. El lote puede quedar aceptado parcialmente.
3. Si recibiste un expediente fuera de la lista, usa **Recibido no relacionado**. Conserva la discrepancia; aceptarlo después requiere confirmar explícitamente ese extra. No lo conviertas en un elemento supuestamente incluido en la lista original.
4. La aceptación crea los ciclos que faltan. **Más acciones → Abrir expediente seleccionado** abre su 360. **Asignar ciclos del folio** exige que todos los ciclos activos estén aceptados y el préstamo abierto; **Asignar** en 360 actúa sobre ese ciclo y permite avanzar recepciones parciales. Una reasignación conserva el historial; marcar colaborador añade apoyo sin sustituir.
5. El mismo CURP/legajo en otro folio reutiliza el maestro y crea otro ciclo. Para legajo 2, captura 2 expresamente. No cambies el folio de un ciclo previo.

## Trabajo diario y validación

En **Expediente 360 → Conteo / incidencias / etapas**, registra los bloques de hojas, confirma el conteo físico y actualiza la etapa conforme al trabajo real. Hoja física, archivo TIFF y página digital son unidades distintas. Un valor desconocido no debe capturarse como cero.

Abre **Codificar TIFF** desde el expediente: importa copias, codifica, corrige o solicita reescaneo. Retirar conserva historia; restaurar deja trazabilidad. Los atajos y el editor siguen descritos en [LAPTOP.md](LAPTOP.md). Nunca edites directamente `originales`, `versiones` ni una carpeta de entrega.

**Organizar y generar reporte** valida, ordena y publica una nueva entrega independiente, vinculando sus métricas. También puedes usar **360 → Entregas → Preparar nueva entrega**. Si faltan códigos, hay TIFF alterados, residuos o reescaneos pendientes, consulta **Validar expediente** y corrige el problema antes de entregar. Después de cambios, una validación anterior puede quedar obsoleta.

En Kanban las cinco columnas se actualizan por recepción, etapa y revisión. Doble clic abre 360. Los filtros incluyen folio, personas, custodia, prioridad, validación y observaciones. **Nota / prioridad** no mueve la etapa. Las tareas manuales antiguas siguen como auxiliares.

## Revisión de una entrega exacta

1. En **360 → Entregas**, selecciona una versión e **Iniciar revisión**. **Ver TIFF de entrega** abre la evidencia congelada, de solo lectura; **Ver manifiesto** comprueba sus archivos.
2. En **Observaciones**, **Nueva sobre entrega seleccionada** permite elegir documento, página, ubicación de hoja física, tipo, descripción, responsable y si bloquea aprobación. Para documento faltante, usa el alcance de expediente completo y describe lo faltante.
3. El digitalizador responde **En corrección**, modifica la copia de trabajo y prepara otra entrega. La edición sola no cierra la observación.
4. En **Responder / validar**, registra **Resuelta**, elige la nueva entrega y escribe qué cambió. El revisor compara la evidencia y marca **Validada** explícitamente. Reabrir o anular también exige motivo.
5. Selecciona la última entrega, inicia su revisión y usa **Aprobar** con evidencia. Se vuelve a comprobar inventario, conteo, recepción y bloqueos. El cierre se registra por esta acción; no se obtiene seleccionando manualmente “Expediente cerrado”. Si hay cambios sin exportar, genera y revisa otra entrega.

La demo permite validar la observación respondida del primer ciclo y aprobar v2 tras revisar su contenido. El segundo ciclo conserva un reescaneo pendiente para practicar. Un ciclo aprobado puede seguir **Prestado a Digitalización**: registra la devolución por separado en **Préstamo → Registrar devolución / custodia**, con quien recibe y acepta.

## Entrega a otra carpeta o equipo

Selecciona la versión correcta y **Exportar a carpeta nueva**. Elige la carpeta contenedora; el programa crea un destino independiente y rechaza uno existente. Lleva la carpeta completa con su `manifest.json`, sin combinarla con una anterior. Conserva el `manifest_hash` mostrado para contrastarlo en destino.

Con el código y su Python/Pillow en el equipo receptor, sin abrir la base:

```bat
.venv\Scripts\python.exe main.py --verificar-entrega "D:\Entregas\CARPETA_NUEVA" --manifest-hash HASH_REGISTRADO
```

Sustituye carpeta y hash por los reales. Sin `--manifest-hash` se comprueba la consistencia interna, pero no que el manifiesto sea el registrado en origen. Una exportación de TIFF no traslada el historial SQLite de revisión; para traslado completo usa [RESPALDOS.md](RESPALDOS.md).

## Carpetas CURP históricas

Abre el ciclo correspondiente. Si no hay folio conocido, usa **Importación y respaldo → Crear ciclo histórico sin folio comprobado**, con CURP y legajo comprobados. La agrupación técnica creada no equivale a un préstamo físico.

En **360 → Importar carpeta CURP**:

1. **Analizar carpeta** realiza el preflight sin cambiar el origen. Lee totales, ubicación, catálogo, duplicados e ilegibles. Un TXT se informa y no se adopta como TIFF.
2. **Registrar análisis** conserva el diagnóstico y las referencias externas. No hace que los TIFF sean archivos gestionados ni los suma como digitalizados activos.
3. **Adoptar copias / reanudar** requiere confirmar el análisis y crea copias verificadas. Si el origen cambió, vuelve a analizar. Una interrupción conserva el registro incompleto y permite reanudar sin repetir las copias confirmadas. No borres la fuente.

Los registros migrados pueden requerir **Confirmar vínculo histórico con el maestro** tras verificar su contexto. Esa confirmación conserva los ciclos separados. Las discrepancias de identidad o fuentes privadas no analizadas requieren revisión de sus evidencias; no se fusionan automáticamente.

## Reportes y continuidad

**Exportar 360 imprimible** guarda HTML local. Ábrelo en el navegador y usa Imprimir o guardar PDF si el sistema dispone de esa función. Incluye identificación, préstamo, asignaciones, métricas conocidas, validación, entregas/cambios, observaciones e historia, incluso antes de escanear.

La interfaz actual ofrece **Indicadores → Exportar indicadores** para los CSV de la vista y su contexto. No exporta automáticamente todo el historial; los datasets del modelo conservan sus funciones propias. Las cifras Excel/CSV legadas se distinguen de los TIFF gestionados; no se suman snapshots. No publiques estos reportes: una instalación real contiene información del expediente.

Antes de trasladar o actualizar una instalación, genera y verifica respaldo completo. Consulta [WINDOWS7.md](WINDOWS7.md) para ensayar en el equipo de oficina sin sustituir sus datos. Para retomar desarrollo, lee [CONTEXTO_PROYECTO.md](CONTEXTO_PROYECTO.md) y [BITACORA_DESARROLLO.md](BITACORA_DESARROLLO.md).
