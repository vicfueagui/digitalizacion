# Ejecución de escritorio en macOS

## Alcance

La aplicación sigue siendo un sistema web Django. Para uso local de escritorio, el lanzador inicia un servidor restringido a `127.0.0.1` y abre el navegador predeterminado. No publica el sistema en la red ni reemplaza el futuro cliente operativo de escritorio.

Estos scripts están preparados y verificados para el entorno actual: macOS 11.7.11, procesador Intel y Python 3.12.

## Primera preparación

1. Instale Python 3.12 si `python3.12 --version` no funciona.
2. Abra Finder y entre en la carpeta del proyecto.
3. Abra la carpeta `scripts`.
4. Haga doble clic en `preparar_macos.command`.

El preparador:

- crea `.venv` cuando no existe;
- instala `requirements.txt`;
- crea `.env` con una clave local aleatoria cuando hace falta;
- restringe los permisos de `.env` al usuario local;
- aplica migraciones;
- carga grupos, permisos y catálogos de forma idempotente;
- ejecuta la comprobación de Django.

macOS puede impedir el primer doble clic porque el archivo proviene de Internet. En ese caso, haga clic secundario sobre el archivo, elija **Abrir** y confirme una sola vez.

## Crear la primera cuenta

Abra Terminal en el proyecto y ejecute:

```bash
./.venv/bin/python manage.py createsuperuser
```

El proyecto no contiene usuarios ni contraseñas predeterminados.

## Iniciar diariamente

Haga doble clic en:

```text
scripts/iniciar_macos.command
```

El navegador abrirá `http://127.0.0.1:8000/`. Mantenga abierta la ventana de Terminal mientras use el sistema. Para detenerlo, vuelva a esa ventana y presione `Control+C`.

También puede iniciarlo desde Terminal:

```bash
cd ~/Documents/project_digitalizacion
./scripts/iniciar_macos.command
```

Para usar otro puerto:

```bash
DIGITALIZACION_PORT=8001 ./scripts/iniciar_macos.command
```

Para una prueba sin abrir automáticamente el navegador:

```bash
DIGITALIZACION_OPEN_BROWSER=0 ./scripts/iniciar_macos.command
```

## Solución de problemas

- **Python no encontrado:** instale Python 3.12 y repita la preparación.
- **Puerto ocupado:** cierre la ejecución anterior o use `DIGITALIZACION_PORT=8001`.
- **No puede iniciar sesión:** cree una cuenta con `createsuperuser` o solicite una cuenta al administrador.
- **Cambió `requirements.txt`:** vuelva a ejecutar `preparar_macos.command`.
- **Cambió el código o aparecieron migraciones:** el lanzador aplica migraciones pendientes antes de iniciar.

## Seguridad

- `.env`, SQLite, archivos importados, TIFF y datos operativos están excluidos de Git.
- El lanzador se enlaza exclusivamente a `127.0.0.1`.
- Esta modalidad es para desarrollo, demostración y uso local controlado; no es el despliegue institucional de producción.
- No copie expedientes reales a esta instalación hasta que estén definidos almacenamiento, permisos, respaldos y políticas institucionales.
