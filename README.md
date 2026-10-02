# Digitalización 0.7.0 · respaldo de código HP

Instantánea preparada el 2026-10-02 desde la instalación de Windows 10. Contiene código, pruebas sintéticas y documentación seleccionada. El usuario autorizó expresamente publicar esta copia en el repositorio público actual. La fecha y el commit efectivos se consultan en el historial de GitHub.

El código de aplicación coincide con la instalación local 0.7.0: núcleo SQLite 8 / TIFF 3. Entorno comprobado previamente: Python 3.8.10 x64, Tk/Tcl 8.6.9, SQLite 3.35.5 y Pillow 9.5.0. Los requisitos de otros perfiles se conservan como antecedentes; `requirements.txt` corresponde al perfil Windows y `requirements-laptop.txt` al perfil Mac. No cambiar el entorno operativo por descargar este respaldo.

## Qué contiene

Aplicación de escritorio Python/Tkinter, SQLite, visor TIFF con Pillow, integraciones numeradas, entregas completas con historial, indicadores y cubo temporal. Incluye las pruebas adicionales de 0.7.0 procedentes de la candidata validada y el exportador local de contexto.

Guías de Ayuda: [integraciones](docs/INTEGRACIONES_V070.md), [recepción e indicadores](docs/RECEPCION_INDICADORES_V061.md) y [operación](docs/OPERACION_V05.md). Los títulos históricos describen su versión de origen; la versión del código es 0.7.0. En la copia de la guía de operación se sustituyó una ruta histórica de perfil local por `/RUTA/DEL/PROYECTO`; el original local se conserva.

[CONTEXTO_CHATGPT.md](CONTEXTO_CHATGPT.md) conserva el resumen de la instalación, sus pruebas y pendientes. Las fuentes canónicas extensas permanecen en el equipo de operación. Este respaldo no incluye todas las bitácoras ni los documentos históricos enlazados desde ellas. No reconstruye el entorno ni sustituye un respaldo de datos.

## Exclusiones deliberadas

Sin SQLite, TIFF, expedientes, Excel/CSV operativos, reportes, logs, resguardos, credenciales, `.env`, entorno virtual, exportaciones de contexto, bundles ni instaladores binarios. Los identificadores y secretos que aparecen en las pruebas son ejemplos ficticios para verificar validaciones. La prueba de fuentes privadas permanece desactivada y sus archivos no se distribuyen.

La selección se fija mediante un manifiesto de rutas y SHA-256 externo al código. `.gitignore` añade protección para el trabajo posterior; no borra archivos rastreados ni limpia historia. No se ha auditado toda la historia del repositorio remoto.

El instalador offline de Pillow necesita su wheel verificado, excluido aquí por ser binario. El generador de documentos históricos conserva referencias a fuentes no distribuidas. Este árbol es respaldo de fuentes y guías seleccionadas, no un paquete instalador completo. La documentación HTML antigua de actualización se omite; no usar sus instrucciones de versiones anteriores para reinstalar 0.7.0.

## Uso seguro

El acceso diario existente sigue siendo `C:\Digitalizacion\INICIAR.bat`. Descargar este código no actualiza la aplicación ni sus datos. No extraerlo sobre operación ni colocar código anterior sobre una base migrada. Cualquier instalación futura requiere su propio respaldo, validación en copia y paquete revisado.

Con el intérprete compatible ya disponible se pueden ejecutar pruebas ficticias desde esta copia:

```powershell
& C:\Digitalizacion\.venv\Scripts\python.exe -B tools\probar_integraciones.py
```

El runner crea un directorio nuevo de pruebas junto a esta copia y limita las escrituras Python a ese directorio. No garantiza control de toda llamada nativa. No habilitar fuentes privadas para probar el respaldo.

`EXPORTAR_CONTEXTO.bat` requiere `.venv` preparada localmente. El exportador no conecta ni sincroniza ChatGPT con el equipo; el usuario adjunta manualmente el texto generado.

La rama de destino es `respaldo/digitalizacion-tk-0.7.0-hp-20261002`. Es una instantánea de la instalación HP; no implica haber fusionado las diferencias de la rama remota 0.6.3. No sustituye esa rama ni `main`, y no configura sincronización automática.

Validación de esta copia en Windows/Python 3.8.10: 30 pruebas aprobadas, cero fallos, errores u omisiones; exportador con datos sensibles ficticios, migración, Tk, BI y entrega/restauración. Gramática 3.8 comprobada aparte en 76 fuentes. Las evidencias locales no se publican automáticamente. El resumen de instalación conserva el estado anterior a esta publicación como antecedente.
