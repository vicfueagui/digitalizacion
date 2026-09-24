# Respaldo del proyecto Python/Tk en GitHub

Repositorio: https://github.com/vicfueagui/digitalizacion

Rama de este proyecto: **respaldo/digitalizacion-tk-0.6.3**.

Al conectar esta carpeta, la rama main contenía una implementación Django diferente (último commit observado: 8e15abb6226e5a1008f3783cd0c9954ba4f28c25). Por eso el proyecto Python/Tk se respalda en una rama independiente con historia propia. No se sobrescribe main ni se mezclan ambas arquitecturas. No fusionar esta rama automáticamente con main.

## Recuperar el código

```sh
git clone --single-branch --branch respaldo/digitalizacion-tk-0.6.3 https://github.com/vicfueagui/digitalizacion.git Digitalizacion-Tk
```

También puedes seleccionar esa rama en GitHub y utilizar Code → Download ZIP. Este ZIP de GitHub es una copia del código; no equivale al paquete de actualización con release-manifest.json. Para generar un paquete utiliza tools/build_release.py y sigue ACTUALIZACION.html. Para trasladar datos reales utiliza MIGRACION_WINDOWS10.html; nunca sustituir producción por un clon.

## Qué se conserva

El primer commit, 3aeb8cf, conserva exactamente los 144 archivos del manifiesto de la entrega0.6.3: código, SQL, pruebas, BAT, documentación y wheel Pillow9.5.0 verificado con su licencia. El siguiente commit añade contexto de Git y exclusiones locales. El código funcional no cambia durante este respaldo.

SHA-256 del ZIP0.6.3 entregado previamente: `6bb70edd4fee959ffd9ad06fb6e795b90722904605194be17653eb4620ba49ec`. Ese ZIP y su huella permanecen localmente en dist; no se regeneran ni sustituyen al crear los commits.

No se publican bases SQLite, TIFF, CSV/Excel de trabajo, fuentes privadas, demos generadas, entornos, credenciales, logs ni carpetas de ensayos. Los ejemplos incluidos en código/pruebas/manuales son sintéticos. El wheel de Pillow es una dependencia distribuible, no un entorno copiado.

GitHub respalda el código; no reemplaza el respaldo completo verificable de datos y documentos. Conserva ambos por sus procedimientos respectivos.

## Guardar cambios posteriores

1. Comprueba `git status` y `git branch --show-current`.
2. Revisa y añade únicamente los archivos de código/documentación correspondientes. No uses opciones de fuerza para añadir datos ignorados.
3. Revisa `git diff --cached --stat` y `git diff --cached` antes de confirmar.
4. Crea un commit descriptivo y ejecuta `git push` hacia la rama de respaldo configurada.
5. Confirma el commit visible en GitHub. No uses force-push ni cambies main para resolver diferencias entre las dos implementaciones.

.gitattributes conserva los bytes de los archivos entre plataformas, incluidos los CRLF de BAT, para evitar alterar hashes al clonar. La identidad Git se configura solo en este repositorio con la cuenta de GitHub y su dirección noreply; no se utiliza la identidad global de ejemplo.

## Validación

Comparación de todos los archivos iniciales contra release-manifest.json y SHA-256, revisión de exclusiones y búsqueda de patrones de credenciales. Pruebas funcionales previas:276 totales/264 aprobadas/12 omitidas/0 fallidas/0 errores en cada perfil Mac3.8.10,3.11.4 y3.13.15. No se repite la suite por cambios exclusivamente de Git/documentación. Windows y producción siguen pendientes según VALIDACION_V063.md.
