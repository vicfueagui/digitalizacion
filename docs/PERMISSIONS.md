# Roles y permisos

Ejecute `python manage.py initialize_system` después de migrar. El comando agrega capacidades base sin crear usuarios.

| Capacidad | Administrador | Responsable | Digitalizador | Revisor | Consulta/auditoría |
|---|:---:|:---:|:---:|:---:|:---:|
| Configuración técnica/usuarios | Sí | No | No | No | No |
| Recibir/importar/conciliar lote | Sí | Sí | No | No | Lectura |
| Ver todos los expedientes | Sí | Sí | Solo asignados | Sí | Sí |
| Asignar/reasignar | Sí | Sí | No | No | No |
| Conteo/incidencia/documento/TIFF | Sí | Sí | Solo asignados | Incidencia según capacidad | No |
| Terminar/enviar corrección | Sí | No por defecto | Solo asignados | No | No |
| Observar/validar | Sí | Sí | No | Sí | No |
| Cerrar validado | Sí | Sí | No | No | No |
| Auditoría/reporte | Sí | Sí | No | Sí | Sí |

Los grupos se llaman `Administradores`, `Responsables de digitalización`, `Digitalizadores`, `Revisores` y `Consulta y auditoría`.

Las capacidades se pueden ajustar desde la administración sin cambiar vistas. Reejecutar el comando repone permisos base, pero no quita permisos adicionales. Ser miembro de Administradores no convierte automáticamente una cuenta en `is_superuser`; use superusuario solo para administración técnica.

La protección se aplica en dos niveles: decoradores de vista y servicios de dominio/consultas acotadas. Un digitalizador obtiene 404 al intentar abrir por URL un expediente ajeno.
