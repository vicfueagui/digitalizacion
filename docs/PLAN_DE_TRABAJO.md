> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

> Documento de la base v0.1. Para el módulo nuevo y sus cambios consulta CODIFICACION.md y VALIDACION_V02.md.

# Plan de construcción y aprendizaje

Proyecto: Digitalización SEGEY — control local y preparación BI.

Tablero sugerido: Pendiente / En curso / En espera / Bloqueada / Hecha. Mantén una sola tarjeta En curso si trabajas tú solo. Etiquetas para una fase futura: Datos, Conteo, Calidad, TIFF, BI, Infraestructura. La v0.1 guarda título, estado, trabajo opcional y notas; no tiene etiquetas aún.

| Orden | Tarjeta | Pasos | Terminado cuando |
|---|---|---|---|
| 1 | Encender el proyecto | Descomprimir, instalar Python, diagnóstico, iniciar | Abre sin errores en el Lanix |
| 2 | Revisar origen | Importar Excel, revisar 55 trabajos y pendientes | Se entienden folio, persona y legajo |
| 3 | Aclarar reglas del área | Confirmar fecha de recepción, f_broche, significado C_folder | Decisiones anotadas y aprobadas por responsable del proceso |
| 4 | Ensayar conteo | Crear folio PRUEBA/2026 y expediente ficticio; 10+10+5; corregir y anular | Confirmación y bitácora coinciden |
| 5 | Ensayar incidencias | Crear tipo, registrar, resolver, desactivar catálogo | El historial se conserva |
| 6 | Revisar codificación | Buscar códigos, corregir descripciones, desactivar obsoletos | Catálogo editable sin códigos duplicados |
| 7 | Vincular los 11 reportes | Ver ruta y alcance de cada reporte | Legajos identificados o CURP completa marcado |
| 8 | Recorrer etapas | Iniciar y terminar procesos en un expediente de ensayo | Cierre exige controles y reapertura deja motivo |
| 9 | Exportar un primer informe | Filtro de folio, exportación, tabla dinámica | No se confunden archivos, hojas y páginas |
| 10 | Piloto de 3 a 5 expedientes | Usar registros nuevos, revisión diaria y respaldo externo | Totales conciliados con el físico y captura cómoda |
| 11 | Organizador TIFF v4 | Especificar folio, legajo, alcance, ID ejecución, rutas por legajo | Pruebas con dos legajos y nombres repetidos sin mezcla |
| 12 | Mejorar interfaces | Atajos, campos grandes, sugerencias de acciones, etiquetas | Se reduce la captura medida en el piloto |
| 13 | BI ampliado | Dimensiones, filtros por fecha de etapa, incidencias frecuentes, tiempos | Cada KPI tiene fórmula, unidad y cobertura de datos |
| 14 | Modernizar equipo | Sistema soportado, Python mantenido y pruebas de restauración | Aplicación operativa en nuevo equipo con mismos registros |
| 15 | Multiusuario | Autenticación, permisos, servidor, PostgreSQL, copias verificadas | Pruebas concurrentes, permisos y migración conciliada |
| 16 | OCR asistido | Muestra representativa, catálogo versionado, evaluación por código | Revisión humana, confianza medible, ningún cambio destructivo automático |

## Cómo hacer cambios manualmente con VS Code

1. Antes de editar, copia el proyecto y crea un respaldo desde la aplicación.
2. Abre la carpeta Digitalizacion desde Archivo > Abrir carpeta.
3. Lee primero README y docs/ARQUITECTURA.md.
4. Haz un cambio pequeño. Interfaz: app/ui.py. Reglas: app/core.py. Importación: app/importers.py.
5. Guarda con Ctrl+S.
6. Cierra y abre la aplicación para cargar el cambio.
7. Ejecuta PROBAR.bat. Si una prueba que antes pasaba falla, corrige o restaura el código.
8. Prueba el flujo con una base separada, no con la operación real.
9. Registra qué cambiaste, por qué y cómo lo comprobaste.

No editar schema.sql esperando que SQLite cambie automáticamente tablas existentes: CREATE TABLE IF NOT EXISTS no migra una tabla ya creada. Se requiere una migración explícita y versionada. No borrar la base para forzar cambios si ya contiene operación real.

## Git opcional, para después

No hace falta Git para abrir o usar la aplicación. El paquete incluye un repositorio transportable llamado repositorio_inicial.bundle, con el código y la documentación, sin el Excel ni CSV privados. Si dispones de Git compatible:

```
git clone repositorio_inicial.bundle Digitalizacion-codigo
cd Digitalizacion-codigo
git status
```

El clon no incluye tus datos. Puedes copiar el Excel y fuentes/registro_digitalizacion_detallado.csv localmente; .gitignore evita agregarlos. No compartas el archivo SQLite ni el ZIP con expedientes.

Cuando quieras registrar un cambio: `git add app docs tests main.py README.md` y `git commit -m "Describe el cambio"`. Configura nombre y correo de autor cuando Git lo solicite. No se creó ni publicó un repositorio en GitHub; el repositorio entregado es local y portable.
