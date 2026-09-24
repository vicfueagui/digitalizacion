> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

> Documento de la base v0.1. Para el módulo nuevo y sus cambios consulta CODIFICACION.md y VALIDACION_V02.md.

# Validación de la entrega 0.1

Fecha: 18 de septiembre de 2026.

Se ejecutaron pruebas en el entorno Linux disponible, con Python 3.12.14, SQLite y los archivos adjuntos originales. La versión exacta del intérprete ejecutor se registra en VALIDACION_ENTORNO.txt. También se verificó la sintaxis con el analizador configurado para Python 3.8.

Pruebas: ver VALIDACION_PRUEBAS.txt generado al empaquetar. Cubren identidad de folio/CURP/legajo, conteo, corrección, baja lógica, reapertura, cierre con requisitos, historial, auditoría con motivo y rollback, catálogos, incidencias, filtros, exportación y fuentes reales. Las pruebas de fuentes usan copias locales; se omiten en el clon Git si no se han copiado los adjuntos privados.

Importación real observada: 55 trabajos, 71 entradas de catálogo, 97 bloques, 12 incidencias, 7 tareas. CSV: 11 ejecuciones válidas, ninguna rechazada. Reimportar no duplica reportes. El original Excel/CSV se comparó por SHA-256 con los adjuntos.

No se ejecutó la aplicación en Windows 7, no se ejecutaron BAT/PowerShell sobre expedientes y no se hizo una validación visual de Tk: este entorno no dispone de servidor gráfico. Se requiere el ensayo local antes de operar expedientes nuevos. No se promete una instalación ya comprobada en el Lanix.

## Comprobación local necesaria

1. DIAGNOSTICO.bat reconoce Python 3.8, SQLite y Tk.
2. INICIAR.bat abre las siete pestañas.
3. Importación Excel y CSV informa los conteos anteriores.
4. En una base de prueba se puede crear folio, trabajo, bloques, incidencia, catálogo y tarea; editar y desactivar.
5. Conteo 10+10+5=25; modificar un bloque y anular otro cambia la suma; Confirmar guarda el total correcto.
6. Un segundo legajo de la misma CURP conserva conteo e incidencias separados.
7. La misma combinación folio/CURP/legajo no se duplica.
8. El CSV reimportado no duplica ejecuciones y estas no se suman para inflar el inventario.
9. Seleccionar filtros cambia tabla, KPI y gráfica. La exportación de trabajos coincide.
10. Cerrar y reabrir conserva datos. Un respaldo puede abrirse como base alternativa para comprobar su integridad.

## Límites actuales

- No hay OCR, visor TIFF, renombrado automático ni integración de escritura con el organizador original.
- Excel es importación inicial; no existe ida y vuelta automática de cambios.
- Los campos legados no expuestos en formularios permanecen en origen.
- Las fechas históricas se conservan pero requieren conciliación; no se transforma C_folder automáticamente en cierre.
- Los KPI son iniciales; no existe una capa completa de medidas DAX ni conexión Power BI preconfigurada.
- Kanban admite cambios de columna mediante formulario, no arrastrar y soltar.
- La auditoría es local y puede ser modificada por quien tenga acceso directo a SQLite; no es una bitácora inviolable.
- La v0.1 no sirve para varios operadores simultáneos, publicación web ni validación oficial de CURP.
