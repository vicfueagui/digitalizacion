# Pasar Digitalización de Windows 7 a Windows 10

Guía del kit **0.6.3**, formato de traslado 1. El programa de trabajo se conserva tal como está en el origen, por ejemplo **0.6.2**. No tienes que actualizar ese programa a 0.6.3 para trasladarlo. El kit trabaja desde otra carpeta.

**Estado de esta entrega:** preparada y ensayada con datos ficticios en Mac. La migración de tus datos reales todavía debe verificarse en las dos computadoras. Ninguna prueba del Mac certifica por sí sola Windows.

## 1. Qué vamos a hacer

Cerrar el sistema viejo → revisar datos → preparar un paquete → copiarlo → verificarlo → restaurar en una carpeta nueva → probar → habilitar el equipo nuevo.

La primera migración usa **Python 3.8.10 de 64 bits, Tk 8.6 y Pillow 9.5.0**, con las mismas versiones de SQLite/Tcl/libtiff que registre el origen. No instales Python moderno para esta operación. No necesitas Docker.

Piensa en el paquete como una caja sellada. El manifiesto es su inventario; SHA-256 es la huella que permite comprobar que su contenido no cambió. El programa comprueba cada documento y todas las tablas de la base; también revisa originales, revisiones e historial.

## 2. Preparar las carpetas sin confundirse

| Nombre | Qué contiene | Ejemplo; puedes elegir otra unidad |
| --- | --- | --- |
| Origen | El programa que funciona y sus datos actuales | C:\Digitalizacion |
| Kit de traslado | Herramientas 0.6.3 extraídas aparte | C:\KitDigitalizacion063 |
| Paquete de migración | Caja verificada que creará el asistente | E:\Traslados\Digitalizacion-Migracion-20260923 |
| Destino nuevo | Instalación que todavía NO debe existir | D:\Archivo\Digitalizacion |

Si los datos están separados del programa, selecciona sus carpetas por separado. La carpeta de datos es la que contiene **datos\digitalizacion.sqlite3**, no la carpeta datos por sí sola. La carpeta del programa contiene **main.py** y **app**.

Usa disco local para producción. Evita carpetas sincronizadas o unidades compartidas mientras opera SQLite. Conserva espacio para dos copias de los datos y margen para pruebas. La herramienta comprueba espacio antes de exportar; una falta de espacio durante una copia bloquea la publicación.

## 3. Comprobar el kit recibido

1. Obtén `Digitalizacion-0.6.3-codigo.zip` y `Digitalizacion-0.6.3-codigo.sha256` por el canal autorizado de tu oficina.
2. Abre el archivo `.sha256` con Bloc de notas. Es una huella de 64 letras y números.
3. Pulsa Windows + R, escribe `cmd` y pulsa Enter. Escribe la siguiente línea cambiando la ubicación si corresponde:

```bat
certutil -hashfile "C:\Traslado\Digitalizacion-0.6.3-codigo.zip" SHA256
```

La huella debe coincidir por completo. La huella recibida por el mismo canal comprueba integridad, no la identidad del remitente; conserva la referencia autorizada.

4. Haz clic derecho en el ZIP → **Extraer todo**. Elige una carpeta nueva para el kit. No pegues archivos encima del programa que funciona.
5. Abre este manual desde el kit. No ejecutes nada dentro de la vista comprimida del ZIP.

## 4. Qué hacer en Windows 7

1. Guarda el trabajo y cierra Digitalización, visores externos y programas que modifiquen los TIFF. Avisa que habrá un cambio de computadora. Nadie debe capturar durante el traslado final.
2. Abre **MIGRAR.bat** desde el kit. Esto no actualiza el programa de producción.
3. Si dice que no encuentra Python, crea con Bloc de notas `python_ruta.txt` en la carpeta del kit. Dentro escribe únicamente la ruta completa del **python.exe que sí funciona**, por ejemplo `C:\Python38\python.exe`. No añadas comandos ni contraseñas. Comprueba que el nombre no termine en `.txt.txt`. Reabre MIGRAR.bat. Si tu instalación funciona con un Python configurado en otro lugar, usa esa ruta; no reinstales el origen por rutina.
4. En **Equipo de origen**, elige **Carpeta de datos del origen** y **Carpeta del programa que funciona**. Pueden ser la misma.
5. Deja desmarcado **Solo laboratorio**. Esa opción sirve únicamente para una demo ficticia.
6. Deja vacía **Raíz histórica probada**, salvo que se haya identificado formalmente una raíz antigua. Un texto viejo de auditoría no requiere por sí solo una reparación. Consulta el apartado de incidencias.
7. Pulsa **Auditar datos** y elige un nombre de carpeta NUEVA fuera del origen para el informe. Debe indicar `correcto: true`, sin problemas. Puedes leer `LEER_DIAGNOSTICO.txt` y `diagnostico.json`.
8. Pulsa **Preparar migración**. En el diálogo escribe el nombre de una carpeta NUEVA, fuera del proyecto y del kit. Aunque el diálogo se parezca a Guardar archivo, el asistente creará una carpeta con ese nombre; no añadas extensión ZIP.
9. Espera **EXPORTACION VERIFICADA**. No cierres la ventana mientras trabaja. Pulsa **Copiar resultado** y guarda ese texto por separado, con fecha y persona responsable. Contiene `sha256_manifiesto` y el identificador del paquete.
10. En **Equipo nuevo** quedarán rellenados paquete y huella. Regresa a **Equipo de origen** y pulsa **Comparar origen con paquete**. Debe decir **MIGRACION VERIFICADA**, sin diferencias.
11. Cierra el asistente. Deja Windows 7 congelado: no vuelvas a abrirlo para capturar mientras se habilita Windows 10. Guarda la hora de corte.

**No copies `.venv`, caches ni una base abierta a mano.** La herramienta toma una copia SQLite consistente que incluye transacciones confirmadas en WAL. Los auxiliares WAL/SHM no se trasladan como documentos sueltos.

## 5. Qué copiar y qué conservar

Copia la **carpeta completa del paquete creado** al medio autorizado y luego al disco de Windows 10. No selecciones solo datos. Conserva también la huella anotada en origen por separado; no la recalcules en destino para sustituir la esperada.

La caja contiene `programa`, `herramientas`, `respaldo`, `informes`, `LEEME.txt`, `migracion-manifest.json` y `migracion-manifest.sha256`. El código original viaja en programa; el kit viaja en herramientas. El manifiesto incluye todos los archivos transferidos.

Conserva el equipo Windows 7, el paquete final y una segunda copia verificada en otro medio autorizado. Conserva respaldos anteriores, fuentes externas y archivos ajenos a datos/reportes en el origen: no se borran ni se trasladan implícitamente. Los reportes gestionados, entregas, originales, revisiones, versiones y auditoría sí viajan.

El paquete contiene datos personales y rutas históricas necesarias para la trazabilidad. No lo envíes completo por correo, mensajería ni a servicios públicos para pedir ayuda. Comparte solo el error y los IDs necesarios, siguiendo las reglas de tu oficina.

## 6. Preparar Windows 10

1. Confirma que Windows 10 sea de **64 bits**: Configuración → Sistema → Acerca de → Tipo de sistema. Ten permisos de escritura en la carpeta elegida.
2. Instala **CPython 3.8.10, Windows installer (64-bit)** desde [la página oficial de Python 3.8.10](https://www.python.org/downloads/release/python-3810/). Mantén Tcl/Tk y pip incluidos. No elijas 32 bits ni paquetes de otro Python. No hace falta modificar PATH.
3. Conserva el instalador utilizado y su procedencia junto a la evidencia técnica, sin cambiar el manifiesto del paquete.
4. Comprueba el SHA del manifiesto recibido, usando la huella guardada en Windows 7:

```bat
certutil -hashfile "D:\Traslados\Digitalizacion-Migracion-20260923\migracion-manifest.json" SHA256
```

5. Para no escribir entornos ni configuración dentro del paquete sellado, extrae también el **kit 0.6.3 verificado** en una carpeta aparte de Windows 10, por ejemplo `D:\KitDigitalizacion063`.
6. Desde ese kit independiente, abre **INSTALAR_VISOR.bat**. Crea y comprueba un entorno local y usa el wheel Pillow 9.5.0 incluido, sin descargar dependencias ni instalarlas globalmente. Si una `.venv` está vacía o dañada, el asistente la conserva y ofrece crear otra carpeta.
7. Si no abre, crea `python_ruta.txt` en el kit con la ruta del Python instalado y repite. La detección comprueba ejecución, versión, 64 bits, Tk, Pillow y libtiff. Un archivo python.exe de cero bytes no es válido.
8. Abre **MIGRAR.bat** en ese kit independiente.

## 7. Restaurar sin sobrescribir nada

1. Ve a **Equipo nuevo**.
2. En **Carpeta del paquete recibido**, selecciona la caja copiada.
3. Pega en **SHA-256 guardado en origen** los 64 caracteres del resultado que conservaste. No pegues el nombre del archivo.
4. Pulsa **Verificar paquete**. Debe indicar **PAQUETE VERIFICADO**. Se comprueban todos sus archivos antes de usar el código capturado.
5. Pulsa **Restaurar en carpeta nueva**. Escribe una ruta NUEVA, por ejemplo `D:\Archivo\Digitalizacion`; la carpeta contenedora `D:\Archivo` sí debe existir.
6. Espera **Datos verificados; falta ensayo y activación**. La aplicación sigue bloqueada por una marca de restauración pendiente. No borres esa marca a mano.
7. Se rellenará **Carpeta de instalación restaurada**. Pulsa **Verificar destino**. Debe decir **MIGRACION VERIFICADA**, con `diferencias: []`.

El destino contiene `programa`, `workspace`, `herramientas`, `evidencia`, `migracion.json` y **INICIAR_MIGRADO.bat**. La base real queda en `workspace\datos\digitalizacion.sqlite3`. No abras el INICIAR antiguo de programa: usa el lanzador migrado después de habilitarlo.

## 8. Ensayar, revisar y habilitar

1. Con la instalación seleccionada, pulsa **Ejecutar ensayo**. Se prueban el kit y el código original, se crea una demo ficticia y se abren ventanas de prueba. Puede tardar varios minutos; no interactúes con las ventanas automáticas.
2. Debe terminar correctamente. Los informes quedan en `ensayos\ensayo-...` dentro del destino. `pruebas.json` corresponde al programa original; `pruebas_herramientas.json`, al kit. Ambos registran aprobadas, omitidas, fallidas y errores. Revisa las omisiones: fuentes privadas no disponibles no equivalen a una prueba de tus datos reales.
3. Pulsa **Abrir demo**. Comprueba teclado, tamaño de texto y visor. En Codificación elige un TIFF de una página y otro con varias; avanza/retrocede por sus páginas. Prueba miniaturas y filtros. Es una demo y sus cambios no afectan producción. Ciérrala para continuar.
4. Confirma que Windows 7 sigue cerrado y que nadie capturó después del corte. Si hubo capturas, no habilites: vuelve a preparar la exportación final y restaura en otro destino nuevo.
5. Marca **Revisé la demo y los TIFF. Windows 7 está cerrado y seguirá congelado**.
6. Pulsa **Habilitar destino**. Se vuelven a comparar datos, archivos, código y runtime, además de comprobar la evidencia del ensayo. El resultado debe indicar **MIGRACION VERIFICADA** y **Producción habilitada**. Un paquete de demo solo puede indicar **Laboratorio habilitado**.
7. Cierra el asistente. En `herramientas\python_ruta.txt` del destino guarda la ruta del intérprete comprobado que figura en el resultado del ensayo. Es configuración local, no modifica el código sellado. Si creaste el entorno con el kit independiente, conserva ese entorno y su ubicación.
8. Abre **INICIAR_MIGRADO.bat**. Crea un acceso directo a ese archivo para el uso diario. Comprueba visualmente varios expedientes reales y TIFF sin editarlos inicialmente, y registra la aceptación de la oficina.

La comprobación automática incluye todas las referencias; la revisión visual confirma además comodidad, teclado y rendimiento en la HP. Si algo no coincide, detente y conserva la evidencia.

## 9. Cuál es la prueba de igualdad

**Comparar origen con paquete** verifica que no cambiaron ni la base lógica —incluido WAL confirmado— ni los documentos. **Verificar destino** compara todas las tablas/filas, relaciones, referencias y hashes contra la copia portable, además del código capturado.

Las rutas activas absolutas del origen pueden convertirse en relativas en la copia. Por eso el archivo SQLite puede tener otro SHA físico legítimamente. Se registra cada conversión y se invierte en una copia temporal para demostrar que las restantes filas, historial y esquema son idénticos. No se modifica el original.

Guarda `evidencia\aceptacion.json`, `migracion.json`, los informes de ensayo y el paquete. **MIGRACION VERIFICADA** es una comparación técnica; la producción solo queda habilitada después del ensayo y confirmación.

Después de nuevas capturas en Windows 10, comparar contra el paquete inicial puede mostrar diferencias legítimas. No vuelvas a habilitar ni restaures encima para hacerlas desaparecer. Usa respaldos actuales y conserva la evidencia del corte inicial. El arranque diario comprueba código y entorno; permite que tus datos sigan evolucionando. Si falla el ejecutable, puede usar otra ruta comprobada con las mismas bibliotecas y deja evidencia del cambio. No acepta una versión de Python/Pillow diferente para resolverlo.

## 10. Si algo falla

| Mensaje o situación | Qué hacer |
| --- | --- |
| Python de 0 bytes, Win32 inválido o acceso denegado | Conserva el entorno dañado. Configura un Python 3.8.10 válido; en destino usa INSTALAR_VISOR para crear un entorno nuevo. No desactives antivirus indiscriminadamente. |
| SHA no coincide | No cambies la huella esperada. Vuelve a copiar desde el paquete original verificado. Si vuelve a fallar, revisa el medio. |
| TIFF faltante o hash diferente | Guarda diagnóstico/IDs. No copies el original encima si su hash es distinto del actual. Un técnico puede reconstruir un candidato exacto con la herramienta de recuperación. |
| Raíz histórica sin evidencia | Déjala sin normalizar. El historial completado se conserva aunque esa ubicación ya no exista. No hagas sustituciones generales de texto en SQLite. |
| Ruta activa externa o traversal | Se detiene. Requiere investigar la referencia real con respaldo; no se remapea arbitrariamente. |
| Hay una operación incompleta | Conserva los archivos y diarios. Resuelve primero la recuperación de la instalación original con su procedimiento probado. |
| Carpeta destino ya existe | No se sobrescribe. Verifica esa ejecución o elige un nombre nuevo. |
| Corte de luz, cierre forzado, disco lleno | La carpeta incompleta no es producción. No borres marcas. Repite desde el paquete intacto en otra carpeta nueva cuando se resuelva la causa. |
| Diferencia en SQLite/Tcl/libtiff | El runtime no es equivalente al origen. Usa los mismos instaladores/bibliotecas; no rebajes controles. |
| Ventanas o pruebas fallan | Guarda logs locales de ensayos. No habilites. Windows 7 continúa como contingencia. |

## 11. Volver atrás correctamente

**Antes de capturar en Windows 10:** cierra el destino. En Windows 7 abre el kit y compara el origen con el paquete final, usando la huella guardada. Si coincide, registra que se cancela el traslado y vuelve a usar únicamente Windows 7. Conserva el destino fallido para analizarlo; no sobrescribas el origen.

**Después de capturar en Windows 10:** el origen viejo ya no contiene todo el trabajo. Cierra ambas instalaciones y guarda un respaldo completo verificable del Windows 10 actual. La vuelta requiere otro traslado/restauración a una carpeta nueva con sus verificaciones y una decisión de corte. Esta versión habilita producción únicamente en Windows 10; no automatiza la activación de una producción nueva en Windows 7. No copies la base vieja sobre la nueva ni mezcles TIFF a mano. Solicita asistencia para preservar las capturas posteriores.

Como mínimo operativo, conserva el origen congelado **30 días después de la aceptación**, y hasta comprobar varios ciclos reales y dos respaldos completos restaurables en medios separados; aplica un plazo mayor si tu política de archivo lo exige. Cumplir el plazo no autoriza borrar originales o historia. No mantengas dos producciones activas.

## 12. Practicar en Mac sin tocar Windows

Usa únicamente demos. Desde la carpeta del kit, con tu Python local de pruebas:

```sh
.venv/bin/python main.py --crear-demo /RUTA/NUEVA/demo
.venv/bin/python migrar.py
```

Selecciona la demo como origen, el código de prueba como programa y marca **Solo laboratorio**. Repite el recorrido a una carpeta nueva fuera del proyecto. Conserva la copia OSX independiente que ya usabas; este ensayo no actualiza sus sesiones. La demo siempre queda identificada como laboratorio.

El Mac no ejecuta BAT, junctions o bloqueos nativos de Windows. Sus resultados se conservan como evidencia local, separados de la aceptación de oficina.

## 13. Después de la migración

Python moderno, cambio de Pillow, empaquetado, OCR y procesamiento en segundo plano se evaluarán en copias ficticias y entregas independientes. Consulta [arquitectura y prueba técnica](docs/MIGRACION_TECNICA.md), [compatibilidad y hoja de ruta](docs/MODERNIZACION.md) y [resultados de esta entrega](docs/VALIDACION_V063.md).

Windows 10 Home/Pro 22H2 terminó su soporte general el 14 de octubre de 2025; edición LTSC y ESU tienen calendarios distintos. El responsable de TI debe comprobar la cobertura de esta HP. Se mantiene el objetivo de traslado conservador; esto no equivale a certificar la seguridad futura del sistema operativo. [Información oficial de Microsoft](https://learn.microsoft.com/en-us/windows/release-health/release-information).
