# Digitalización en el navegador · candidata 0.8.0

Esta interfaz se está validando con expedientes ficticios. El acceso habitual de operación sigue siendo INICIAR.bat. No utilices la candidata con una base real hasta completar la transición validada.

## Abrir la demostración

Ejecuta `C:\Digitalizacion\VER_DEMO_WEB.bat`. Abre el navegador en `http://127.0.0.1:8765`. Usuario de demostración: `operador_ficticio`. Contraseña exclusivamente ficticia: `ClaveFicticiaWeb_2026!`. Ninguna de estas credenciales sirve para operación real. La consola del BAT mantiene el servidor activo; ciérralo con Ctrl+C al terminar. Si el puerto está ocupado por esta misma demo, abre directamente la dirección del navegador.

## Un recorrido de oficina

Si aparece un error de formulario o CSRF después de una actualización, detén la consola de la demo con Ctrl+C y vuelve a ejecutar VER_DEMO_WEB.bat. Abre una página nueva en http://127.0.0.1:8765/acceso/ y recarga con Ctrl+F5 antes de iniciar sesión. Una pestaña que se abrió antes de otro inicio de sesión puede contener un formulario vencido: usa «Volver a abrir el acceso» o «Volver al sistema». No reenvíes la página anterior con Atrás. No es necesario activar DEBUG ni deshabilitar CSRF.

1. Entra con tu usuario. El sistema registra quién realiza cada cambio. Tu función determina qué acciones puedes confirmar.
2. Abre Recepción y folios. Registra el folio y sus datos de entrega física. Importa la lista o añade los elementos esperados. Una lista importada no acredita recepción.
3. Coteja CURP, nombre y legajo contra el expediente físico. Acepta únicamente los elementos comprobados. Los faltantes y discrepancias requieren aclaración propia. Usa Desglosar legajos si hay varios físicos de la misma persona.
4. Abre el expediente, asigna al digitalizador y registra los bloques de hojas. Confirma el conteo cuando termines. Hoja física, TIFF y página son unidades diferentes.
5. Importa copias TIFF. Selecciona cada archivo para revisarlo y asignarle el código documental. Puedes girar o recortar la página seleccionada conservando las revisiones. Para un escaneo defectuoso, solicita reescaneo y registra la hoja física afectada.
6. Valida el expediente. Atiende documentos sin código, incidencias, reescaneos y conteos pendientes antes de continuar.
7. Organizar / entregar genera una NUEVA entrega del expediente completo actualizado. Las versiones anteriores permanecen intactas. Abre el manifiesto y sus páginas para revisar exactamente esa entrega.
8. Registra observaciones si procede. La corrección debe generar una entrega posterior; el revisor valida la respuesta. La aprobación explícita cierra la etapa. La devolución física del préstamo se registra por separado.

## Si llegan documentos adicionales

Primero aprueba la entrega anterior. Desde el expediente, elige Nueva integración, registra recepción real, acuse, motivo y responsable. Cuenta únicamente las hojas que acaban de llegar. Importa y codifica los nuevos TIFF, valida y genera otra entrega completa. No dupliques el expediente ni reutilices el conteo anterior para las hojas nuevas.

## Cómo decidir qué sigue

Mi jornada muestra el inventario vigente, las etapas y los expedientes con fecha objetivo vencida. La fecha objetivo es un compromiso de trabajo, no un plazo legal calculado por el sistema. Tablero permite buscar por nombre/CURP, folio, responsable y prioridad sin recargar toda la página. Abrir una tarjeta muestra los pasos y requisitos del expediente; mover una tarjeta visualmente no acredita que una etapa se haya completado.

## TIFF y teclado

Dentro del visor: F7/F8 cambia de documento; RePág/AvPág cambia de página; + y - ajusta el zoom; F ajusta la imagen; F2 abre renombrar; Ctrl+O abre importar; Ctrl+A selecciona los documentos visibles; Supr abre retiro con confirmación y motivo. Los atajos no actúan mientras escribes en un campo. Ver retirados permite seleccionar y recuperar versiones. No se borran los originales.

Retirar y recuperar son acciones por lote con progreso por archivo: si hubo un error, revisa cuáles terminaron y cuáles siguen pendientes. El sistema conserva solicitudes iniciadas para evitar que un doble clic repita una escritura.

## Indicadores

Selecciona año, mes, semana ISO o día, y desglosa por folio, digitalizador o etapa. Inventario por recepción usa la recepción del lote y sus documentos vigentes. Ingresos TIFF usa la importación registrada y puede incluir documentos retirados después; no demuestra el momento físico de escaneo. Fechas desconocidas se muestran aparte. El CSV respeta los filtros y protege fórmulas al abrirse en una hoja de cálculo. Custódialo como información del expediente.

## Respaldo y cierre

Administración permite crear y verificar un respaldo privado de expedientes, TIFF, entregas, usuarios, permisos y solicitudes. Conserva una instantánea exacta de la base de origen y otra portable, además de las versiones y huellas del código. La restauración se hace en una carpeta nueva y conserva las cuentas; exige volver a iniciar sesión. El respaldo no incluye el intérprete ni una copia ejecutable del código: conserva por separado el paquete de instalación verificado.

No subas bases, TIFF, usuarios, reportes o respaldos a GitHub. Para terminar, cierra sesión y detén el servidor con Ctrl+C en su ventana de inicio. No abras al mismo tiempo Tk y la web sobre el mismo workspace.

## Alcance de esta candidata

Se ejecuta únicamente en el equipo local, sin abrir puertos de la oficina ni publicar Internet. Conserva SQLite y las reglas existentes; no se ha migrado a PostgreSQL ni habilitado trabajo simultáneo entre equipos. Una red multiusuario requiere definir servidor, permisos, respaldo y administración de infraestructura. Python 3.8 y el acceso diario anterior se conservan durante la validación.
