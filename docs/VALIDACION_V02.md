> **Documento histórico anterior a 0.4.** Para rutas, actualización y resultados vigentes consulta [README](../README.md) y [VALIDACION_V04](VALIDACION_V04.md).

> Documento histórico v0.2. La versión 0.3 cambia identidad, atajos, correcciones y visor: consulta CAMBIOS_V03.md.

# Validación v0.2

42 pruebas automatizadas aprobadas: 24 previas y 18 nuevas. Python 3.12.14, Pillow 12.3.0, Linux. Sintaxis compatible con Python 3.8 verificada. El wheel Pillow 9.5.0 para CPython 3.8 Windows x64 se incluye íntegro, con licencia y SHA-256; no se ejecutó en este entorno.

Las nuevas pruebas verifican importación sin modificar origen, duplicados idénticos, separación de legajos, nombres repetidos sin sobrescritura, atajos persistentes y colisiones, TIFF de varias páginas, DPI, preservación de páginas no editadas, modos binario/RGB, restauración original, recortes inválidos, rollback de nombre y edición cuando falla la auditoría, bloqueo por falta de código o cambios externos, conflictos en destino, inventario enlazado sin doble conteo, invalidación al editar, carpeta definida por catálogo, recuperación de un renombrado interrumpido y coherencia de las 66 métricas.

No se verificó visualmente la interfaz ni sus atajos en un escritorio Windows. Prueba local necesaria:

1. Respalda y aplica actualización; ejecuta INSTALAR_VISOR.bat.
2. En un trabajo de ensayo importa dos TIFF de una página y uno de varias páginas.
3. Confirma que se ve texto legible, ajusta zoom y recorre todas las páginas.
4. Abre Atajos, consulta una secuencia, enfoca el visor y ejecútala; verifica nombre y siguiente archivo. Repite el mismo código en otro TIFF para comprobar sufijos.
5. Comprueba que escribir en el buscador no renombra archivos.
6. Recorta/rota una página, compara vista sin cambios, descarta y vuelve a editar. Guarda. Reabre el TIFF y verifica todas las páginas.
7. Confirma que el archivo externo seleccionado al importar sigue intacto.
8. Previsualiza organización; comprueba folio/CURP/legajo y destinos. Confirma.
9. Revisa Reportes TIFF e Indicadores. Organizar de nuevo no aumenta existencias.
10. Cierra y abre, verifica atajos persistentes, archivos e inventario. Respalda datos completo.

Si aparece error, conserva el mensaje exacto y los archivos originales. No elimines la base ni la carpeta del trabajo para intentar solucionarlo.
