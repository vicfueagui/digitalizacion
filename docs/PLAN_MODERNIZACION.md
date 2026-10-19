# Plan de modernización · edición pública

Estado de esta instantánea: 0.8.2-dev instalada y verificada en la HP con núcleo 8 / TIFF 4. Este respaldo contiene código y guías, no datos ni acceso a la oficina. Las rutas privadas y documentos históricos completos se conservan localmente.

## Decisiones vigentes

Servicios Python y SQLite existentes; Django LTS para autenticación, formularios y permisos; HTMX y recursos locales para interacción; Chart.js para visualizaciones. Trabajador serial y bloqueo de workspace. Dependencias fijadas en requirements-modern.txt. No se introdujo otra aplicación frontend ni pandas, OCR, nube o red multiusuario.

La etiqueta dev permanece porque el paquete aceptado se instaló sin renombrar código. El negocio mantiene compatibilidad 3.8; el servidor usa el runtime moderno. Las versiones verificadas y guías están en README. No modificar .development ni el entorno usado por una instalación existente sin recrearlo y validar sus rutas.

## Siguiente etapa

- Observar una jornada humana, teclado físico, zoom, legibilidad y rendimiento con imágenes representativas.
- Atender incidencias concretas primero en copia candidata y datos ficticios; registrar pruebas realmente ejecutadas y límites.
- Conservar recuperación compatible con TIFF 4, código, cuentas y capturas posteriores. No repetir la primera transición ni restaurar sobre trabajo nuevo.
- Evaluar HTTPS, PostgreSQL y servidor de oficina únicamente si se define operación desde varios equipos; no están configurados.
- Respaldos GitHub futuros requieren petición explícita; esta publicación no configura sincronización automática.

La instalación autorizada y la publicación de código son tareas distintas. Este respaldo no altera el sistema diario, no instala dependencias y no autoriza futuras migraciones de datos. Contexto, bitácora pública y validación resumida documentan esta instantánea; la evidencia operativa permanece privada.
