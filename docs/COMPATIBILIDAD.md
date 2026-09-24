# Matriz vigente para el kit0.6.3

Consulta [MODERNIZACION.md](MODERNIZACION.md) y [VALIDACION_V063.md](VALIDACION_V063.md): se ejecutaron CPython3.8.10 y3.13.15 reales en Mac, manteniendo perfiles independientes. La aceptación Win7→Win10 permanece pendiente de oficina. La información siguiente documenta los entornos anteriores.

# Compatibilidad y soporte — consulta del 21 de septiembre de 2026

| Entorno | Versiones | Verificación en esta entrega | Límites |
|---|---|---|---|
| MacBook Pro Intel, macOS 11.7.11 Big Sur, 16 GB | Python 3.11.4; SQLite 3.42.0; Tcl/Tk 8.6.12; Pillow 12.3.0 | Suite sintética, ventana Tk, aplicación/visor, demo y respaldo/restauración | No representa Windows ni valida cada gesto de trackpad/Retina |
| Perfil alterno de API en el mismo Mac | Python 3.11.4 + Pillow 9.5.0 | Consultar resultado actual en VALIDACION_V062.md | No es Python 3.8 ni el wheel Windows |
| Lanix Windows 7 SP1 Professional x64, Core 2 Duo, 3 GB | Objetivo Python 3.8.10 + Pillow 9.5.0 cp38 win_amd64 | Código conserva sintaxis Python 3.8; wheel legado con SHA-256; falta ensayo físico | Windows, BAT, locking msvcrt, NTFS, teclado y rendimiento pendientes de oficina |
| Otros macOS/Linux | No fijados ni certificados | Script POSIX disponible; no se ejecutó Linux en esta entrega | Crear entorno propio y verificar Tk/Pillow/sistema |
| Docker en este Mac | Cliente encontrado 24.0.6 | Solo se leyó versión; motor no iniciado | Big Sur fuera del soporte actual; no se usa para esta entrega |

## Dependencias comprobadas

El instalador de [Python 3.11.4 para Mac](https://www.python.org/downloads/release/python-3114/) declara macOS 10.9 o posterior; se utiliza el intérprete que ya tenía este equipo. El perfil reproducible de desarrollo no equivale a afirmar que ese parche antiguo esté actualizado en seguridad. La [rama Python 3.11](https://devguide.python.org/versions/) está en mantenimiento de seguridad; la actualización del intérprete del sistema queda para una intervención administrada, con su propio ensayo de Tk.

[Pillow admite Python 3.11 en las ramas 12 y 9.5](https://pillow.readthedocs.io/en/stable/installation/python-support.html). Se fijó 12.3.0 en `requirements-laptop.txt` después de instalar y ejecutar su wheel `cp311-cp311-macosx_10_10_x86_64`. Consulta [notas oficiales de 12.3.0](https://pillow.readthedocs.io/en/stable/releasenotes/12.3.0.html). No se fuerza Pillow 9.5 sobre cualquier Python moderno.

Se conserva [Python 3.8.10](https://www.python.org/downloads/release/python-3810/) y el wheel Pillow 9.5.0 incluido para Windows x64. `requirements.txt` conserva el pin legado; `requirements-legacy.txt` lo hace explícito. El instalador comprueba plataforma, versión, arquitectura, entorno virtual y huella antes de instalar sin red. Python 3.8 terminó soporte el 7 de octubre de 2024, según el [ciclo oficial de Python](https://devguide.python.org/versions/).

[Tkinter recomienda abrir `python -m tkinter`](https://docs.python.org/3/library/tkinter.html) para probar la instalación. Aquí se abrió esa ventana y además se ejecutó una prueba de la aplicación con TIFF sintéticos. Las pruebas de eventos simulados no certifican distribuciones físicas de teclado.

## Docker

No se recomienda usarlo en este equipo concreto. La [política oficial de Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) admite la versión actual de macOS y las dos anteriores, con al menos 4 GB RAM. Big Sur queda fuera; tener 16 GB y un cliente antiguo no resuelve el soporte. No se propone instalar una versión obsoleta ni servidores de ventanas. En un equipo soportado podría servir para pruebas Linux, previa revisión institucional de licencia, pero no validaría Windows 7, BAT ni la GUI de Mac. Se añadió únicamente una exclusión preventiva de datos (`.dockerignore`).

## Ruta hacia un sistema soportado

[Windows 7 terminó soporte extendido en 2020 y su programa ESU en 2023](https://learn.microsoft.com/en-us/lifecycle/products/windows-7). Se conserva como transición local, no como destino sostenible.

El [soporte general de Windows 10 terminó el 14 de octubre de 2025](https://support.microsoft.com/en-us/windows/deployment/updates-lifecycle/windows-10-support-has-ended-on-october-14-2025). Una futura instalación de Windows 10 no garantiza soporte: TI debe identificar edición, versión, licencia y cobertura ESU/LTSC aplicable antes de elegirla. No se ha comprobado elegibilidad institucional ni se ha comprado una licencia.

La ruta recomendada es evaluar un equipo compatible con un sistema vigente, probar escáner/impresora/visor y luego restaurar una copia verificada. [Windows 11 exige al menos 4 GB RAM, CPU compatible, UEFI y TPM 2.0](https://www.microsoft.com/en-us/windows/windows-11-specifications); los 3 GB declarados del Lanix ya son insuficientes y el resto del hardware requiere evaluación. No se propone saltarse requisitos. Linux soportado es otra evaluación posible si los dispositivos y procesos del área lo permiten; no se ha elegido distribución ni se cambia el SO para desarrollar ahora.

Big Sur también debe quedar en la hoja de ruta de renovación administrada. Consulta el [historial de actualizaciones de seguridad de Apple](https://support.apple.com/en-us/100100) y compatibilidad del modelo exacto; el número del sistema no demuestra por sí solo cobertura vigente. No se modificó macOS en esta intervención.
