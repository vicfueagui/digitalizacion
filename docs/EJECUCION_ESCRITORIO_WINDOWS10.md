# Ejecución de escritorio en Windows 10

## Alcance

La aplicación es un sistema web Django. En Windows 10, el lanzador inicia el servidor en `127.0.0.1` y abre el navegador predeterminado. No publica el sistema en la red ni instala servicios de producción.

El entorno virtual de Windows se guarda en `.venv-windows`. No copie ni reutilice `.venv` de macOS o Linux porque los entornos virtuales no son portables entre sistemas operativos.

## Requisitos

1. Windows 10 de 64 bits con actualizaciones instaladas.
2. Python 3.12 o posterior obtenido de `python.org`.
3. Durante la instalación de Python, active **Add Python to PATH** y conserve el Python Launcher.
4. Una copia o clon del repositorio.

Para clonar con Git:

```bat
git clone https://github.com/vicfueagui/digitalizacion.git
cd digitalizacion
```

También puede descargar el ZIP desde GitHub y extraerlo completamente antes de continuar.

## Primera preparación

Desde el Explorador de archivos:

1. Abra la carpeta `digitalizacion`.
2. Abra `scripts`.
3. Haga doble clic en `preparar_windows10.cmd`.
4. Espere el mensaje **Preparación terminada correctamente**.

El script:

- localiza Python 3.12;
- crea `.venv-windows`;
- instala las dependencias;
- crea `.env` con una clave aleatoria cuando hace falta;
- aplica migraciones;
- carga grupos, permisos y catálogos;
- ejecuta la comprobación de Django.

Si SmartScreen bloquea el archivo, verifique que el repositorio sea el oficial y utilice **Más información → Ejecutar de todas formas**. No ejecute una copia cuyo origen no pueda comprobar.

## Crear la primera cuenta

Abra CMD o PowerShell dentro de la carpeta del proyecto y ejecute:

```bat
.venv-windows\Scripts\python.exe manage.py createsuperuser
```

El proyecto no incluye cuentas ni contraseñas predeterminadas.

## Iniciar diariamente

Haga doble clic en:

```text
scripts\iniciar_windows10.cmd
```

El navegador abrirá:

```text
http://127.0.0.1:8000/
```

Mantenga abierta la ventana de CMD. Para detener el servidor, presione `Control+C` y confirme si Windows lo solicita.

También puede iniciarlo desde CMD:

```bat
cd C:\ruta\al\proyecto\digitalizacion
scripts\iniciar_windows10.cmd
```

Para cambiar el puerto en CMD:

```bat
set DIGITALIZACION_PORT=8001
scripts\iniciar_windows10.cmd
```

En PowerShell:

```powershell
$env:DIGITALIZACION_PORT = "8001"
.\scripts\iniciar_windows10.cmd
```

## Solución de problemas

- **Python no encontrado:** reinstale Python 3.12 activando **Add Python to PATH**.
- **`.venv-windows` no es utilizable:** renómbrelo y ejecute otra vez la preparación; no reutilice entornos de otro sistema.
- **Puerto ocupado:** cierre la ejecución anterior o seleccione otro puerto.
- **No puede iniciar sesión:** cree un superusuario o solicite una cuenta al administrador.
- **Cambió `requirements.txt`:** repita `preparar_windows10.cmd`.
- **El navegador no abre:** visite manualmente `http://127.0.0.1:8000/`.

## Seguridad

- `.env`, `.venv-windows`, SQLite, Excel, TIFF y datos operativos están excluidos de Git.
- El servidor escucha exclusivamente en `127.0.0.1`.
- No permita el acceso por firewall ni cambie el host a `0.0.0.0` para uso institucional.
- Este modo es apropiado para desarrollo y demostración local, no para producción multiusuario.
- No utilice expedientes reales hasta definir almacenamiento, respaldos, permisos y políticas institucionales.
