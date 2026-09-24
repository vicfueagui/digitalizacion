# Respaldo, restauración y traslado

Hay dos tipos de respaldo. El automático al cerrar y antes de migrar/importar es un snapshot **solo SQLite**, obtenido con la API `Connection.backup`. El botón **Respaldar base y TIFF**, `--respaldar` y el actualizador producen un respaldo **completo** con los documentos y reportes gestionados. Una copia SQLite sola no permite recuperar los TIFF.

## Ensayo completo en el Mac

Cierra la demo antes de usar los comandos. Ejecuta desde Terminal:

```sh
cd "/Users/admin/Downloads/Digitalizacion"
.venv/bin/python main.py --workspace ensayos/modelo-operativo-v05/demo --respaldar demos/respaldo-demo-01
.venv/bin/python main.py --verificar-respaldo demos/respaldo-demo-01
.venv/bin/python main.py --restaurar demos/respaldo-demo-01 --destino demos/demo-restaurada-01
.venv/bin/python main.py --workspace demos/demo-restaurada-01
```

Los destinos de respaldo/restauración deben ser nuevos. Si ya los usaste, cambia el sufijo `01` por otro. Se comprueba SHA-256 de cada archivo, integridad SQLite, relaciones y huellas de TIFF originales, activos, retirados y revisiones. El manifiesto debe incluir todos los documentos referenciados; se rechazan rutas absolutas, saltos de carpeta, nombres incompatibles con Windows, colisiones por mayúsculas/acentos y enlaces, incluso internos. Un archivo faltante o alterado detiene el procedimiento. Un respaldo que falla conserva una marca `INCOMPLETO.txt` y no se acepta como restaurable.

La copia SQLite usa la API de respaldo, también cuando el origen trabaja con WAL. El archivo exportado se convierte a modo de journal independiente; no depende del `-wal` del equipo de origen. Los TIFF se copian con un bloqueo de aplicación; no se abre otra instancia del mismo espacio. Cierra versiones antiguas y herramientas externas que no conocen ese bloqueo.

`--respaldar` abre la base existente para lectura y **no la migra**. La exportación normaliza las columnas conocidas de rutas y los destinos del diario **en la copia SQLite**, verificando que cada ruta pertenece a la raíz de origen. No hace sustituciones de texto globales ni cambia la base productiva. Rutas Windows relativas con `\` se resuelven como componentes portables; nuevas rutas usan `/`. El marcador de demostración también se conserva al respaldar una demo. Una ruta absoluta de otro equipo, una referencia fuera de raíz o un enlace que sale de ella requieren revisión y detienen el respaldo. No se adivina una equivalencia entre `C:\...` y una carpeta Mac.

El respaldo completo incluye `datos/` y `reportes/`; no incluye el escáner externo, Excel/CSV originales importados, respaldos anteriores, software ni `.venv`. Conserva esas fuentes iniciales mediante el procedimiento institucional que corresponda. El actualizador además guarda por separado los archivos de código que reemplazará. Los respaldos no están cifrados: deben almacenarse en un medio local autorizado, igual que el resto del expediente.

## Restauración en Windows, sin reemplazar producción

Desde el código nuevo extraído, con su `.venv` local (ajusta las rutas reales):

```bat
cd /d "C:\ActualizacionDigitalizacion062"
.venv\Scripts\python.exe main.py --verificar-respaldo "D:\Resguardos\antes062"
.venv\Scripts\python.exe main.py --restaurar "D:\Resguardos\antes062" --destino "C:\PruebasDigitalizacion\restauracion062"
.venv\Scripts\python.exe main.py --workspace "C:\PruebasDigitalizacion\restauracion062" --diagnostico
.venv\Scripts\python.exe main.py --workspace "C:\PruebasDigitalizacion\restauracion062"
```

Una restauración interrumpida deja `.restauracion_incompleta` y la aplicación rechaza abrirla; repite en otra carpeta nueva conservando la evidencia.

Resultado esperado: respaldo íntegro, destino nuevo creado, `Integridad: ok`, expedientes e imágenes visibles. La primera apertura puede migrar esta **copia restaurada** y no afecta al origen. La validación humana debe comparar IDs/folios/legajos, conteos, incidencias, varias páginas y el inventario.

El actualizador permite [recuperar solo código](WINDOWS7.md#si-hay-un-fallo) si los datos siguen exactamente como antes de actualizar. Una base migrada o nueva captura bloquea esa opción. Para recuperar en otra carpeta la versión anterior, restaura `datos_antes` a una nueva raíz y coloca allí los archivos de `codigo_antes` conservando sus rutas. El snapshot pertenece al estado anterior a actualizar. Usa el Python y Pillow de Windows; no copies `.venv` desde otro sistema. Decide la vuelta a producción solo después de revisar la copia y cualquier captura posterior.

## Reglas del traslado

Git o el ZIP de actualización transportan código. La información operativa se traslada con un respaldo completo verificado y una decisión explícita de dónde seguirá la operación. No transportes solo una base abierta; no sincronices bidireccionalmente SQLite, WAL y TIFF. No actives dos copias productivas del mismo expediente.

La lectura del diagnóstico no cambia el esquema. Abrir normalmente una base antigua sí ejecuta las migraciones compatibles. Si no quieres migrar ni siquiera una copia todavía, usa `--diagnostico`.

## Nuevos documentos gestionados en 0.5.0

El respaldo completo incluye `datos/versiones/`, `datos/entregas/`, originales, copias activas/retiradas y revisiones, además de SQLite y reportes. Verifica todas las referencias de versiones y las entregas publicadas (manifiesto y archivos exactos). Nunca edites un manifiesto para cambiar sus rutas: las rutas internas son relativas y el hash debe conservarse. Los auxiliares SQLite `-wal`, `-shm` y `-journal` se excluyen antes de resolver sus rutas; las transacciones confirmadas quedan en el snapshot generado con la API de SQLite.

Las fuentes históricas registradas como externas y las copias de entregas exportadas fuera del workspace no se incluyen. Las entregas originales gestionadas sí permanecen en `datos/entregas`. Conserva también las fuentes externas mediante el procedimiento de archivo aplicable. El almacenamiento aumenta con las versiones y entregas independientes; comprueba espacio disponible para ellas y para el resguardo completo.

## Listas y directorio de 0.6.0

La base respaldada incluye directorio/alias, referencias, metadatos declarados, filas originales importadas y vínculo del desglose de legajos. El CSV/XLSX externo permanece en su ubicación: su hash y contenido tabular quedan en SQLite, pero el respaldo no recoge automáticamente ese archivo externo. Consérvalo según tu procedimiento de archivo. La migración núcleo 7 conserva los documentos y las entregas previas.
