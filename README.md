# Sistema de Digitalización de Expedientes SEGEY

Aplicación web Django para dar trazabilidad al proceso del Archivo General desde la recepción de un lote hasta la revisión y cierre de cada expediente. Separa expresamente hojas físicas, páginas digitales, archivos TIFF y documentos lógicos; conserva asignaciones, reconteos, observaciones y cambios de estado.

Este MVP no hace OCR, clasificación por IA ni movimientos de TIFF. El inventario de carpetas es de solo lectura.

## Funciones disponibles

- autenticación, grupos y permisos por capacidad;
- recepción de lotes y asociación de una fuente oficial;
- importación `.xlsx` con mapeo explícito, SHA-256 y filas originales;
- conciliación de filas oficiales y expedientes físicos;
- asignación y custodia histórica;
- conteos físicos versionados e incidencias configurables;
- inicio, terminación, observación, corrección, validación y cierre;
- documentos lógicos, modalidades y metadatos TIFF separados;
- inventario TIFF de solo lectura e importación de CSV del BAT v2;
- conciliaciones, reporte operativo y auditoría append-only.

## Instalación paso a paso en macOS 11.7.11

Abra Terminal y ejecute cada bloque en orden. Las instrucciones parten de que el proyecto está en `~/Documents/project_digitalizacion`.

1. Compruebe Python 3.12:

   ```bash
   python3.12 --version
   ```

   Debe mostrar `Python 3.12.x`. Si el comando no existe, instale la versión 3.12 para macOS desde el instalador oficial de Python, cierre Terminal, vuelva a abrirla y repita la comprobación.

2. Entre al proyecto y cree un entorno aislado:

   ```bash
   cd ~/Documents/project_digitalizacion
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

   Al inicio de la línea de Terminal debe aparecer `(.venv)`.

3. Instale las dependencias:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

4. Cree la configuración local:

   ```bash
   cp .env.example .env
   ```

   Para desarrollo local puede conservar SQLite. Cambie `DJANGO_SECRET_KEY` por una cadena larga y privada. El archivo `.env` no se versiona.

5. Prepare la base de datos y los catálogos:

   ```bash
   python manage.py migrate
   python manage.py initialize_system
   ```

   El segundo comando es idempotente: puede repetirse. Crea Federal/Estatal, DP/FP/HL y los grupos iniciales, pero nunca crea usuarios ni contraseñas.

6. Cree la primera cuenta administradora:

   ```bash
   python manage.py createsuperuser
   ```

7. Ejecute las pruebas:

   ```bash
   python manage.py test
   ```

   Para revisar también imports y errores estáticos de Python, instale las herramientas de desarrollo y ejecute:

   ```bash
   python -m pip install -r requirements-dev.txt
   ruff check apps config tests
   ```

8. Arranque el servidor local:

   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

   Abra `http://127.0.0.1:8000/`. La administración está en `http://127.0.0.1:8000/admin/`.

9. En Administración, cree las cuentas reales y asigne cada una al grupo correcto. No marque como superusuario a responsables o revisores solamente por su función operativa.

Para salir del entorno virtual use `deactivate`. En una terminal nueva, vuelva a ejecutar `source .venv/bin/activate` antes de los comandos del proyecto.

## Primer recorrido funcional

1. Ingrese como responsable y seleccione **Lotes > Recibir lote**.
2. Abra el lote e importe el Excel indicando exactamente sus encabezados y valores.
3. Revise filas aceptadas/erróneas y cree los expedientes desde la fuente.
4. Registre por separado cualquier expediente físico sin fila oficial.
5. Abra un expediente y asígnelo a un digitalizador.
6. El digitalizador confirma la recepción y correspondencia, inicia, captura hojas físicas e incidencias, registra modalidades/TIFF y envía a revisión.
7. Un usuario distinto con permiso de revisión observa o valida.
8. Un responsable cierra definitivamente un expediente ya validado.

## Configuración

Las variables están documentadas en `.env.example`. Las más importantes son:

- `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`;
- `DB_ENGINE` y variables `POSTGRES_*`;
- `MAX_IMPORT_FILE_BYTES` y `MEDIA_ROOT`;
- `SCANNER_INBOX_ROOT` y `DIGITAL_REPOSITORY_ROOT`;
- cookies seguras, redirección HTTPS y HSTS para producción.

Para PostgreSQL instale `requirements-production.txt`. El servidor de desarrollo no debe usarse en producción.

## Documentación

- [Arquitectura](docs/ARCHITECTURE.md)
- [Modelo de dominio](docs/DOMAIN_MODEL.md)
- [Flujo y estados](docs/WORKFLOW.md)
- [Permisos](docs/PERMISSIONS.md)
- [Importación Excel](docs/IMPORT_EXCEL.md)
- [Integración con BAT](docs/BAT_INTEGRATION.md)
- [Plan](docs/IMPLEMENTATION_PLAN.md)
- [Preguntas abiertas](docs/OPEN_QUESTIONS.md)

Las fuentes funcionales originales en la raíz se conservan sin modificaciones.
