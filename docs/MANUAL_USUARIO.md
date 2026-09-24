# Manual de uso de Digitalización

**Versión 0.6.2 · Guía para quien recibe, digitaliza, revisa o consulta expedientes.** Puedes leerla sin internet, buscar con Ctrl+F y volver a ella desde **Ayuda** en la ventana principal. En Mac, usa Cmd+F en el navegador. Los ejemplos y nombres de práctica son ficticios; no los captures en producción.

Si tu tarea es instalar una versión nueva, empieza por [Actualizar paso a paso](../ACTUALIZACION.html). Aquí aprenderás a trabajar con el sistema y a resolver situaciones habituales. Los nombres en negritas son pestañas, botones o acciones de la aplicación.

## 1. Qué representa cada cosa

| Concepto | En palabras sencillas | Ejemplo ficticio |
| --- | --- | --- |
| CURP | Identifica a la persona a la que pertenece el expediente. | La misma persona puede tener más de un legajo. |
| Legajo | Un expediente físico de esa CURP que se controla por separado. | Legajo 1 y legajo 2 tienen conteos e imágenes diferentes. |
| Expediente maestro | La combinación de CURP y número de legajo. | CURP de ejemplo + legajo 2. |
| Folio | El número del formato con el que un área relaciona uno o varios expedientes. | LISTA-DEMO/2026 puede incluir tres personas. |
| Préstamo / recepción | Registra qué físicos se esperaban, qué llegó y su custodia. | Llegaron dos expedientes y faltó uno. |
| Ciclo o trabajo | El trabajo de ese legajo dentro de un folio. | El legajo 1 vuelve otro año bajo un folio distinto. |
| Hoja física | Una hoja de papel que cuentas. | Una hoja escrita por ambos lados sigue siendo una hoja. |
| TIFF | Un archivo digital. Puede contener una o varias páginas. | Un TIFF de 3 páginas cuenta como 1 archivo y 3 páginas. |
| Entrega | Una versión congelada de los documentos preparados para revisar. | v1 se corrige; v2 conserva las correcciones sin borrar v1. |
| Observación | Algo que el revisor solicita corregir en una entrega concreta. | Página 2 girada en un TIFF de v1. |
| Validación | Comprobación del expediente y de sus archivos. | Detecta un código ausente o un reescaneo pendiente. |

**Importar la lista no confirma que el papel llegó. Aprobar la entrega digital no registra la devolución física.** Son pasos separados para poder seguir el trabajo real. Una CURP con dos legajos conserva dos expedientes maestros, enlazados por la persona; no juntes sus imágenes en un mismo ciclo.

## 2. Abrir el sistema y orientarte

En Windows abre **INICIAR.bat** en tu carpeta habitual. El nombre de la versión aparece en el título. En el laboratorio Mac usa el acceso del Escritorio indicado en [LAPTOP.md](LAPTOP.md); cierra una sesión antes de abrir la misma demo desde otra versión. El acceso **061** conservado corresponde a 0.6.1: para probar cambios de 0.6.2 usa una copia de ese paquete, como indica el apartado 24.

**Cambiar operador** identifica a quien está registrando las acciones. Escribe el nombre acordado por tu oficina antes de empezar el turno. Es una identificación de auditoría local, no un inicio de sesión con contraseña. La aplicación trabaja con un operador por espacio de datos; no abras el mismo espacio desde dos ventanas o equipos a la vez.

| Pestaña | Cuándo utilizarla |
| --- | --- |
| Expedientes | Buscar un expediente, abrir su 360, contar o codificar sus TIFF. |
| Folios | Importar listas, cotejar los físicos, aceptar, asignar y registrar devoluciones. |
| Indicadores | Ver cantidades, etapas, coberturas y detalle de una vista filtrada. |
| Kanban | Seguir el avance y abrir el trabajo que requiere atención. |
| Catálogos | Mantener áreas, personas, sistemas, ubicaciones y catálogos documentales. |
| Reportes TIFF | Consultar y vincular declaraciones históricas importadas. |
| Importación y respaldo | Importaciones históricas, pendientes, bitácora y respaldo completo. |

Haz clic en una fila antes de pulsar una acción sobre ella. **Cancelar** cierra la captura pendiente de ese diálogo sin guardarla; no revierte operaciones que ya confirmaste antes. Si una lista parece vacía, revisa primero sus filtros y usa **Limpiar** donde esté disponible.

## 3. El recorrido de un expediente

1. Importar la lista del folio o registrar el folio y sus elementos esperados.
2. Cotejar el papel con la lista, definir los legajos y aceptar los elementos recibidos.
3. Registrar quién entregó y recibió; asignar el trabajo al digitalizador.
4. Contar y confirmar las hojas físicas; registrar incidencias cuando corresponda.
5. Escanear con la herramienta del escáner e importar los TIFF al legajo correcto.
6. Codificar, revisar las páginas y corregir o reescanear lo necesario.
7. Validar y preparar una entrega.
8. Revisar esa entrega exacta, atender observaciones y generar otra versión si hay cambios.
9. Aprobar la última entrega y cerrar el ciclo digital cuando pase las comprobaciones.
10. Registrar por separado la devolución del papel y hacer respaldo completo.

No necesitas terminar un folio entero para avanzar los elementos que sí llegaron y fueron aceptados. Mantén visibles los faltantes y las diferencias para darles seguimiento.

## 4. Primer ejercicio con datos ficticios

Haz este recorrido **en una demo**, cuyo título diga DEMOSTRACIÓN FICTICIA. Si no tienes una, consulta el apartado 24 o la prueba del asistente de actualización.

1. Abre **Folios → Importar lista Excel / CSV**.
2. Busca `ejemplos/lista_folio_sintetica.csv` dentro de la carpeta de tu demo.
3. Revisa que folio, CURP y nombre estén en sus columnas correspondientes. Deja **Legajo si falta** vacío.
4. Pulsa **Actualizar vista previa** y después **Confirmar importación**. La lista trae tres personas ficticias del folio `LISTA-DEMO/2026`.
5. Pulsa **Continuar con recepción**. Si la cerraste, selecciona ese folio y abre **Recepción / préstamo**.
6. Selecciona los tres registros con **Seleccionar visibles**. Pulsa **Aceptar seleccionados**.
7. En este ejercicio simula que cotejaste un físico por cada CURP. Comprueba la propuesta **legajo 1**, marca la confirmación de cotejo y pulsa **Aceptar y crear expedientes**.
8. Pulsa **Ver en Expedientes**. Deben aparecer los tres ciclos del folio, sin volver a escribir sus CURP.
9. Ve a **Indicadores** y filtra por `LISTA-DEMO/2026`. Deben aparecer tres expedientes, tres CURP y recepción aceptada en los tres, si partiste de una demo nueva y no añadiste legajos. Importar y aceptar esa lista no agrega TIFF.
10. En Folios añade un segundo legajo a una de esas CURP siguiendo el apartado 7, acepta ese nuevo físico y vuelve al resumen. Debes tener cuatro expedientes y tres CURP para ese folio.

Si ya habías hecho el ejercicio con el mismo archivo y configuración, el sistema lo reconocerá: no creará de nuevo los mismos elementos. Para repetir desde cero, crea otra demo con un nombre nuevo; no borres registros para simular un comienzo.

## 5. Importar la lista de Excel o CSV

Usa **Importar lista Excel / CSV** en Folios o la acción equivalente de Expedientes. **Importar Excel inicial** pertenece a la carga histórica de una base sin trabajos; no es el botón para las listas diarias de préstamo.

### Preparar el archivo

Se admiten `.xlsx`, `.csv` y `.tsv`. Si recibes un Excel antiguo `.xls`, guarda una **copia** como `.xlsx` o CSV desde Excel y conserva el original. Coloca los encabezados en una fila y un registro en cada fila siguiente. Revisa que el programa de hojas de cálculo no transforme el folio en fecha ni cambie las CURP. El orden de las columnas puede variar.

| Encabezado de una lista | Qué debes comprobar |
| --- | --- |
| CURP O RFC | Debe contener una CURP válida para crear el expediente. Un RFC solo no se convierte en CURP. |
| No. | Es el consecutivo de la lista. No representa el legajo. |
| APELLIDO PATERNO, MATERNO, NOMBRE | Corresponde al nombre de la persona. |
| CURP O RFC2 | Es la segunda identidad declarada; si difiere, revisa la discrepancia. |
| Integra | Conserva quién aparece como integrador; no asigna automáticamente al digitalizador. |
| folio | Relaciona la fila con el formato de entrega. |
| sistema | Dato declarado del sistema de origen. |
| fecha solicitud | Fecha del pedido original; no acredita la recepción del físico. |
| TRABAJADOS | Texto declarado por la fuente; no cierra ni avanza el expediente por sí mismo. |

El ejemplo de la demo contiene una fila como esta, con datos inventados:

| CURP O RFC | No. | Nombre | folio | fecha solicitud | TRABAJADOS |
| --- | --- | --- | --- | --- | --- |
| IIII900103HYNDDD03 | 1 | Persona ficticia de lista 1 | LISTA-DEMO/2026 | 18/8/2026 | NO TRABAJADO |

### Revisar y confirmar

1. Selecciona el archivo. En Excel elige la **Hoja** correcta.
2. Revisa **Fila de encabezado**. Si hay un título sobre la tabla, indica la fila donde empiezan realmente los encabezados y pulsa **Leer encabezados**.
3. En **Correspondencia de encabezados**, compara cada campo con su columna. Si el nombre no fue reconocido, escoge la columna manualmente. No uses una columna diferente solo para eliminar un aviso.
4. Si toda la lista carece de folio, escribe el valor comprobado en **Folio si falta**. Puedes elegir un área común. Esos valores completan faltantes; revisa siempre la vista previa.
5. Si el archivo no indica legajo, deja **Legajo si falta** vacío. Se puede confirmar en recepción. Un legajo común solo se usa cuando ya comprobaste que aplica a todas las filas afectadas.
6. Pulsa **Actualizar vista previa**. Lee los totales de válidas, por revisar y sin legajo. Revisa el detalle de las filas dudosas.
7. Pulsa **Confirmar importación**. Guarda o anota el resultado. Para un único folio, **Continuar con recepción** abre el siguiente paso; con varios folios, entra a cada uno desde la pestaña Folios.

**Resultado esperado:** las CURP válidas y sus folios quedan registrados con procedencia. Las filas con errores quedan como pendientes; no se fabrican identidades. Una fila sin legajo puede aparecer en Folios antes de disponer de un ciclo en Expedientes.

Si cambias columnas, hoja o valores comunes, hay que actualizar otra vez la vista previa. Si el archivo cambió después de previsualizarlo, vuelve a leerlo: el sistema evita confirmar una fuente distinta de la revisada.

### Duplicados y errores de origen

Importar exactamente el mismo archivo, hoja y configuración muestra que el lote ya existe. No duplica ni vuelve a procesar automáticamente las filas que quedaron pendientes. Revisa esas filas en **Importación y respaldo → Ver fuente de pendiente**. Corrige una copia de la fuente y vuelve a previsualizarla, o concilia el elemento mediante la acción operativa correspondiente. Los registros válidos que ya existen se reutilizan sin sobrescribir su trabajo.

**Marcar pendiente revisado** solo registra que lo revisaste; no corrige una CURP, no crea legajos, no recupera un archivo faltante ni vincula por sí mismo un reporte. Haz primero la corrección comprobable.

## 6. Recibir sin volver a escribir las CURP

1. Selecciona el folio en **Folios** y abre **Recepción / préstamo**.
2. Compara la lista en pantalla con los expedientes físicos entregados. Busca por CURP o nombre si la lista es larga.
3. Selecciona solo los que cotejaste. **Seleccionar visibles** toma las filas que muestran los filtros actuales. Shift selecciona un rango; Ctrl en Windows o Cmd en Mac permite seleccionar varios.
4. Pulsa **Aceptar seleccionados**. Comprueba la vista previa de CURP, nombre, legajo y resultado de cada elemento.
5. Para registros sin legajo, el diálogo propone **1** de forma visible. Cámbialo si corresponde. Esa propuesta solo completa los que no tenían legajo; conserva los ya registrados. Si una CURP tiene varios físicos, define primero el desglose del apartado 7.
6. Marca **He cotejado estos expedientes físicos…**. Añade una nota si ayuda a documentar el caso.
7. Pulsa **Aceptar y crear expedientes**. Luego **Ver en Expedientes** para continuar el trabajo del folio.

**Resultado esperado:** recepción aceptada y ciclos disponibles sin recapturar las CURP. Cancelar la vista previa no modifica la recepción. Repetir la misma aceptación no duplica los expedientes ni sustituye su evidencia previa. Si hay un error al guardar la selección, la operación completa se revierte.

Cuando falta, se registra la fecha de recepción individual al aceptar. El área, la persona que entrega, quien recibe y el acuse global se capturan aparte en **Más acciones → Registrar entrega / recepción del folio**. No uses la fecha de solicitud del Excel como sustituto de una recepción desconocida. Una recepción histórica requiere la fecha y evidencia comprobadas.

## 7. Varios legajos de la misma CURP

**Caso práctico:** la lista contiene una persona, pero recibes tres expedientes físicos rotulados legajo 1, 2 y 3.

1. En el préstamo del folio, selecciona el elemento de esa CURP.
2. Abre **Más acciones → Registrar / añadir legajos**.
3. Indica los números comprobados de los legajos, siguiendo el formato del diálogo, por ejemplo `1,2,3`, y la evidencia del desglose.
4. Guarda y revisa la lista resultante. Acepta únicamente los físicos que realmente llegaron.
5. En Expedientes usa **Ver / añadir legajos de la misma CURP** o, en 360, **Legajos de esta CURP** para navegar entre ellos.

Cada legajo tendrá sus propios conteos, TIFF, entregas y revisiones. Conserva el vínculo con la CURP y el origen de la lista. Añadir legajos no duplica los TIFF del primero ni acredita por sí solo su recepción.

**Si ya aceptaste legajo 1 y después llega legajo 2**, añade el 2 y acepta ese nuevo físico. No cambies el número del legajo 1 para reutilizarlo, ni metas los archivos del 2 en el primero.

**Si el mismo legajo regresa en otro folio**, registra el nuevo folio y su elemento. El sistema reutiliza su identidad maestra y conserva otro ciclo. En **Registros asociados** puedes consultar los ciclos y **Usar como registro principal** el que corresponda, sin fusionar o borrar la historia. El folio de un ciclo previo no se cambia para representar una nueva entrega física.

## 8. Recepción parcial, faltantes y diferencias

| Situación | Acción recomendada | Qué conservar |
| --- | --- | --- |
| Llegaron 8 de los 10 físicos esperados | Acepta los 8 cotejados. Para los otros, usa Revisar diferencia y registra Faltante o Pendiente según lo comprobado. | Evidencia de lo recibido y de lo pendiente. |
| La CURP de la carátula no coincide con la lista | Selecciona el elemento → Revisar diferencia → Discrepancia. | Dato esperado, dato visto y motivo. No aceptes por parecido de nombre. |
| Llegó un expediente fuera de la lista | Más acciones → Recibido no relacionado. | La condición de extra y la evidencia; aceptarlo requiere confirmación expresa. |
| Faltaba un legajo y llega más tarde | Añádelo si aún no existe; revisa su estado individual y acepta tras cotejarlo. | Fecha y evidencia de esa recepción. |
| Se aceptó algo equivocadamente | Revisa el elemento individual y deja el motivo de la corrección. Si ya hay trabajo, examina su 360 antes de cambiar el estado. | Historia y documentos; no borres la identidad para ocultar el error. |

La aceptación rápida detiene selecciones que contienen discrepancias, faltantes, identidades repetidas o préstamos en devolución. Usa **Revisar diferencia** para resolver cada excepción con evidencia. No cambia estos casos silenciosamente.

**Caso parcial:** puedes avanzar los 8 aceptados asignándolos desde el 360 de cada ciclo. **Asignar ciclos del folio** exige que los ciclos activos de ese folio estén aceptados y el préstamo siga abierto; si hay pendientes, la asignación completa puede ser rechazada.

## 9. Áreas, responsables y catálogos reutilizables

En **Catálogos** abre el directorio de áreas, responsables, sistemas y ubicaciones. También puedes mantener estos datos con los botones **+** y **Editar** junto a los selectores de los formularios.

1. Elige el tipo de registro que necesitas y busca primero si ya existe.
2. Pulsa **Nuevo**, escribe el nombre con el criterio acordado por tu oficina y guarda. Ejemplo ficticio: `Archivo de demostración`.
3. Regresa al formulario y selecciona ese valor. La próxima vez podrás reutilizarlo sin escribirlo completo.
4. Para corregir un nombre, selecciona su registro → **Editar** y escribe el motivo.
5. Si deja de utilizarse, pulsa **Desactivar / reactivar** con motivo. Para recuperarlo, marca **Incluir bajas**, selecciónalo y reactívalo.

La baja no elimina préstamos ni asignaciones anteriores. Renombrar conserva los textos históricos ya registrados y el vínculo con el mismo registro. Si alguien cambió de nombre o función, revisa si corresponde editar el registro o dar de alta a otra persona; no sustituyas una identidad por otra.

Los catálogos documentales y de incidencias son distintos del directorio de personas. En los documentos, selecciona el tipo correcto y revisa código, título, descripción y carpeta. Los códigos existentes no se reutilizan para significados diferentes. Desactivar impide nuevas selecciones; no elimina su uso previo.

## 10. Asignar y reasignar el trabajo

1. Abre **Expediente 360 → Asignar** para un ciclo aceptado, o **Más acciones → Asignar ciclos del folio** para el folio completo cuando cumpla las condiciones.
2. Elige al digitalizador del directorio y escribe el motivo o referencia de asignación.
3. Guarda y revisa el responsable que aparece en el resumen y en la tabla.

Si otra persona continúa el trabajo, registra una **reasignación** con motivo. Conserva el historial anterior. Si solo brinda apoyo, usa la opción de colaborador del formulario; esa acción no sustituye al titular.

El campo **Integra** del Excel no hace esta asignación. Tampoco basta con escribir una nota: la asignación operativa se registra con su acción específica. El préstamo debe estar abierto y el elemento aceptado para asignar.

## 11. Buscar expedientes y leer la tabla

Escribe parte de la CURP, el nombre, el folio o el digitalizador en los filtros de **Expedientes**. La lista se actualiza tras una breve pausa al escribir, sin pulsar Buscar. Es un filtro local; no necesita internet. Si escribes una fecha incompleta, completa el formato que pide la pantalla antes de interpretar el resultado.

La tabla prioriza CURP, nombre, folio, legajo, estado, TIFF activos, páginas, hojas físicas, digitalizador y recepción. **TIFF y páginas corresponden al inventario activo del ciclo vigente mostrado**. No suman versiones retiradas, entregas anteriores ni declaraciones de un reporte legado.

Un filtro por folio puede encontrar una identidad a través de sus ciclos históricos; la fila principal conserva el ciclo elegido como principal. Usa **Registros asociados** si necesitas trabajar específicamente con el folio anterior. No cambies el principal solo para hacer coincidir una cifra sin revisar cuál ciclo estás abriendo.

**Caso “no encuentro lo que acabo de importar”:** limpia filtros, revisa el folio en Folios y comprueba si tiene legajo y recepción aceptada. Un elemento sin ciclo sigue en la lista del préstamo. Revisa también **Incluir inactivos** si fue desactivado. No vuelvas a crear el expediente inmediatamente.

## 12. Expediente 360, conteo e incidencias

**Expediente 360** reúne el resumen del ciclo, préstamo, asignaciones, entregas, observaciones, análisis de carpetas e historia. Comprueba CURP, folio y legajo al abrirlo. Pulsa **Actualizar resumen** después de cambios en otras ventanas.

### Contar las hojas físicas

1. Entra a **Conteo / incidencias / etapas → Conteo**.
2. Cuenta un bloque manejable de hojas, escribe su cantidad y pulsa **Agregar (Enter)**. Repite por bloques.
3. Si un bloque está mal, selecciónalo y usa **Corregir**. Si se capturó de más, **Anular bloque**, dejando el motivo cuando se solicite.
4. Revisa la suma y pulsa **Confirmar total**. El mensaje indica el total físico confirmado.

Ejemplo: cuentas 40 hojas, luego 35 y finalmente 5 que estaban fuera del broche. Registra bloques 40, 35 y 5: total **80 hojas**. Las de fuera del broche ya están incluidas; no vuelvas a sumarlas. Un dato desconocido se deja pendiente, no se captura como cero.

Hoja física, página y archivo TIFF son unidades diferentes. Si esas 80 hojas se escanean por ambos lados, podrías obtener más de 80 páginas. Revisa las diferencias y su evidencia; no ajustes el conteo físico únicamente para que coincida con el digital.

### Registrar una incidencia

En la pestaña **Incidencias**, crea el registro con el tipo del catálogo, cantidad si corresponde, detalle y ubicación física. Por ejemplo: “Hoja rota entre separadores 2 y 3; texto inferior ilegible”. Usa **Resolver** cuando se atendió o **Anular** si fue una captura errónea, conservando motivo. Una incidencia física no sustituye una observación sobre una entrega digital concreta.

### Aplicar la etapa real

En **Etapas e historial**, elige la siguiente etapa y pulsa **Aplicar etapa**. Registra el motivo cuando se pida. La secuencia de trabajo contempla: Recibido, Conteo en curso, Conteo completado, Escaneo en curso, Expediente escaneado, Codificación en curso, Expediente codificado, Revisión en curso, Correcciones solicitadas, Correcciones en curso, Listo para aprobación y Expediente cerrado.

Avanza una etapa a la vez conforme al trabajo; un retroceso requiere motivo. Las fechas se registran al aplicar la acción. **Expediente cerrado** se obtiene mediante aprobación de la entrega, no forzando el último estado desde un selector. El flujo de revisión registra sus acciones propias; revisa siempre el historial en vez de simular trabajo que no ocurrió.

## 13. Importar TIFF y acomodar la pantalla de codificación

El sistema recibe archivos que ya generó el escáner; no controla el hardware del escáner. Verifica primero que todos pertenezcan a la CURP y legajo seleccionados.

1. En Expedientes selecciona el ciclo y pulsa **Codificar TIFF**.
2. Lee el folio, CURP y legajo del título.
3. Abre **Importar → Archivos TIFF…** para escoger archivos o **Importar → Carpeta…** para una carpeta. Revisa la confirmación del expediente antes de copiar.
4. Selecciona un archivo en el panel izquierdo. La imagen aparece al centro y el catálogo a la derecha.
5. Comprueba el contador **Página … / …**; revisa todas las páginas de un TIFF multipágina.

El sistema trabaja con copias gestionadas y conserva originales/versiones. No edites desde el Explorador las carpetas internas `originales`, `versiones` o `entregas`. Conserva la fuente del escáner hasta verificar la importación conforme al procedimiento de tu oficina.

### Vistas de archivos y espacio de trabajo

| Acción | Cómo hacerla |
| --- | --- |
| Ver columnas o una lista compacta | Cambia a Detalles o Lista en el panel de archivos. |
| Reconocer imágenes rápidamente | Elige Miniaturas. Muestran la primera página y el número de páginas, no todo el documento. |
| Agrandar miniaturas | Coloca el puntero sobre ese panel y usa Ctrl + rueda, o el control de tamaño. |
| Recorrer archivos | Usa la rueda sin Ctrl en el panel izquierdo. |
| Dar más espacio a la imagen o al catálogo | Arrastra el separador vertical entre los paneles. |
| Ocultar/restablecer paneles | Revisa las opciones del menú Vista. F11 amplía la imagen. |
| Ver todo el ancho/alto de una página | Pulsa Ajustar. 100% muestra escala natural. |
| Ampliar la imagen central | Usa la rueda sobre la imagen. Shift + rueda desplaza. |
| Mover la página ampliada | Arrastra la imagen cuando no esté activado Recortar. |

Los botones compactos quedan junto a la imagen; las acciones menos frecuentes están en **Importar**, **Archivo**, **Editar** y **Vista**. En equipos con poca memoria usa **Ajustar** y evita un zoom excesivo. La app limita el tamaño de la vista previa y solo carga miniaturas visibles; una imagen grande todavía puede tardar.

## 14. Codificar y corregir una imagen

### Asignar el tipo documental

1. Selecciona el TIFF y lee su contenido.
2. Busca el documento en el catálogo de la derecha por código o descripción.
3. Selecciona el código y pulsa **Asignar código**, o haz doble clic en él.
4. Comprueba el código resultante. Si está activado **Avanzar al codificar**, se seleccionará el siguiente TIFF.

La codificación corresponde al TIFF completo. No asignes un código sin revisar las páginas adicionales. Si se mezclaron tipos documentales en un archivo, organiza el material y reescanea según el procedimiento operativo; no supongas que cada página tiene un código independiente.

Los atajos permiten mantener Ctrl, teclear la secuencia numérica del código y soltar Ctrl. Para códigos HL se usa Ctrl+Shift y la secuencia. Consulta **Atajos** para el catálogo disponible. En Mac, la tecla Command no sustituye a Ctrl para codificar. Si el teclado numérico no responde como esperas, prueba con el botón del catálogo y revisa el teclado físico antes de usarlo en serie.

### Girar, enderezar y recortar

1. Sitúate en la página correcta con **‹ Pág. / Pág. ›**.
2. Usa los botones de giro de 90° o **Editar → Otro ángulo…** para enderezar.
3. Para recortar, activa **Recortar** y marca el área que quieres conservar. Comprueba que no elimine información.
4. Usa **Deshacer** si el ajuste es incorrecto. **Sin ajustes** permite comparar la vista sin los ajustes pendientes: no restaura el original histórico.
5. Pulsa **Guardar** para registrar la edición. Al cambiar de archivo o cerrar con cambios pendientes, elige guardar, descartar o cancelar según lo que quieras conservar.

Los atajos de navegación son F7/F8 para archivos y RePág/AvPág para páginas. Ctrl+S guarda y Ctrl+Z deshace ajustes pendientes. No interpretes una miniatura pequeña como prueba de legibilidad: revisa la imagen central.

Para consultar revisiones u originales, usa **Archivo → Historial / originales…**. Restaurar una versión exige motivo y conserva el historial. No borres la revisión anterior para “limpiar” el expediente.

## 15. Reescaneo, retiro y recuperación de documentos

**Caso: la página 2 de un TIFF de tres páginas está cortada.**

1. Selecciona el archivo y ubica la página afectada.
2. Usa **Archivo → Marcar reescaneo…**. Indica página, ubicación en el físico y motivo preciso: “Falta el margen derecho”.
3. En **Archivo → Reescaneos…**, consulta o exporta la lista para localizar el papel.
4. Reescanea con la herramienta del escáner e importa el nuevo TIFF al mismo ciclo.
5. Usa la acción de vincular/sustituir de Reescaneos y comprueba páginas y alcance. Sustituir una página y sustituir un TIFF completo son operaciones distintas; sigue la opción que corresponda al material nuevo. El sistema valida que el reemplazo no elimine las demás páginas de un multipágina.
6. Revisa la imagen resultante y organiza/prepara otra entrega. La entrega previa sigue existiendo; no se modifica su evidencia.

**Si un TIFF no pertenece al expediente**, usa **Archivo → Retirar TIFF…** con motivo. Se excluye del inventario activo y de la siguiente entrega; no se borran originales ni entregas previas. Para recuperarlo, abre **TIFF retirados…** y restaura el que corresponda dejando evidencia.

**Si una operación quedó interrumpida**, conserva el mensaje y usa **Archivo → Recuperar operación…** cuando corresponda al diario pendiente. No renombres archivos a mano para quitar el aviso. Si no puede recuperarse, conserva los registros y pide revisión técnica antes de seguir editando ese ciclo.

## 16. Validar y preparar una entrega

1. Confirma el conteo físico y revisa códigos, páginas, incidencias y reescaneos pendientes.
2. En 360 pulsa **Validar expediente**. Lee los problemas y atiende los que bloquean. Una validación puede tener advertencias que requieren revisión, aunque no todas impidan la entrega.
3. En Codificación pulsa **Organizar / entregar**, revisa el plan y pulsa **Confirmar organización**. La alternativa de 360 es **Entregas → Preparar nueva entrega**.
4. Revisa que aparezca una nueva versión en **Entregas**. Selecciónala y abre **Ver TIFF de entrega** y **Ver manifiesto**.

**Resultado esperado:** una entrega independiente con sus archivos y manifiesto. El manifiesto es la lista de qué archivos exactos contiene y sus huellas de comprobación. No lo edites con Bloc de notas ni combines dos carpetas de entregas.

Cambiar una imagen, retirarla, recodificarla o modificar datos relevantes puede dejar obsoleta una validación anterior. Después de corregir, vuelve a validar y prepara otra entrega. Las copias de v1 y v2 no se suman como si fueran documentos activos adicionales.

Si hay un bloqueo, revisa el problema concreto. Un reporte histórico que dice “terminado” no sustituye documentos gestionados ni una entrega aprobada. No uses un BAT organizador antiguo sobre las copias internas del sistema.

## 17. Revisar, observar, corregir y aprobar

### Abrir la evidencia correcta

En **360 → Entregas**, selecciona la versión y pulsa **Iniciar revisión**. **Ver TIFF de entrega** abre la copia exacta de esa versión, de solo lectura. Examinar la copia de trabajo no garantiza estar viendo lo que se entregó al revisor.

### Registrar una observación

1. Con la entrega seleccionada y su revisión iniciada, abre **Observaciones → Nueva sobre entrega seleccionada**.
2. Elige el documento de esa entrega, página si corresponde, tipo de observación, descripción y responsable.
3. Añade la ubicación de la hoja física para facilitar el reescaneo. Señala si la observación bloquea la aprobación.
4. Para un documento faltante, elige el alcance de expediente completo/documento faltante y describe lo que falta. No asignes una página inexistente a otro TIFF.

Ejemplo: “En v1, página 2 del documento seleccionado, el texto del borde derecho está cortado; físico después del separador 3”. Es más útil que escribir únicamente “corregir imagen”.

### Atender y validar la corrección

1. El digitalizador abre **Responder / validar**, registra **En corrección** y atiende el problema en la copia de trabajo.
2. Valida y prepara una nueva entrega, por ejemplo v2.
3. En la observación registra **Resuelta**, señala la entrega v2 y describe qué cambió. Editar el TIFF por sí solo no resuelve la observación.
4. El revisor abre **Ver evidencia exacta**, comprueba la corrección y marca **Validada** con evidencia. Si sigue mal, usa la transición de reapertura disponible con motivo; no la valida para que desaparezca del listado.
5. Para anular una observación capturada por error, conserva el motivo mediante la acción correspondiente.

### Aprobar

Selecciona la **última entrega** del ciclo, inicia su revisión y pulsa **Aprobar**, escribiendo evidencia. El sistema vuelve a comprobar recepción, conteo, archivos, vigencia y observaciones bloqueantes. Si el inventario cambió después de la entrega, prepara y revisa otra versión.

La aprobación registra el cierre digital. En la demo, el primer ciclo contiene una observación respondida y una entrega v2 para practicar la validación y aprobación. El segundo conserva un reescaneo pendiente para practicar su bloqueo.

## 18. Devolver el expediente físico

La devolución se lleva por folio/préstamo. Antes de registrar una acción global, comprueba qué físicos comprende y el acuse correspondiente.

1. Desde 360 pulsa **Préstamo**, o entra desde Folios a **Recepción / préstamo**.
2. Abre **Más acciones → Registrar devolución / custodia**.
3. Registra el estado que realmente corresponda. La secuencia habitual es **Prestado a Digitalización → En devolución → Devuelto → Devolución aceptada**.
4. Captura quién recibe, fecha y referencia o evidencia. Para Devuelto y Devolución aceptada debe identificarse quien recibe.
5. Revisa el resultado en el préstamo y conserva el comprobante físico conforme a tu oficina.

Un ciclo puede estar digitalmente cerrado mientras el papel continúa prestado. También puede existir una incidencia de custodia. Regístrala con su motivo; no marques una devolución completa si todavía quedan físicos sin entregar o sin acuse.

## 19. Exportar una entrega o un resumen

**Para entregar TIFF:** en **360 → Entregas**, selecciona la versión y pulsa **Exportar a carpeta nueva**. Elige la carpeta contenedora; el sistema crea un destino independiente. Lleva la carpeta completa, incluido `manifest.json`, y conserva el `manifest_hash` que identifica esa entrega. No mezcles su contenido con el de una exportación previa.

Quien recibe puede verificarla sin abrir la base de datos. Desde cmd, usando el código y Python del equipo receptor:

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\Digitalizacion\main.py" --verificar-entrega "D:\Entregas\CARPETA_RECIBIDA" --manifest-hash HASH_REGISTRADO
```

Sustituye la carpeta y `HASH_REGISTRADO` por los valores reales; no escribas literalmente ese marcador. Sin la opción de hash se comprueba la consistencia interna, pero no se contrasta con la huella que guardaste en origen. Una entrega exportada no contiene toda la base ni el historial de revisión: para trasladar el sistema completo se usa un respaldo.

**Para consulta o impresión:** pulsa **Exportar 360 imprimible**. El sistema muestra la ubicación del HTML. Ábrelo en un navegador y utiliza Imprimir. Puedes guardar PDF si el sistema tiene esa opción. El resumen incluye datos del ciclo incluso si todavía no tiene escaneos. En una instalación real estos reportes contienen información de expedientes; compártelos por los canales autorizados.

## 20. Entender y utilizar Indicadores

Los filtros se comparten con Expedientes: CURP/nombre, folio, digitalizador, estado y fechas de recepción. El texto superior indica el alcance y momento de actualización. **Limpiar** recupera el ámbito sin esos filtros. Las fechas se refieren a recepción, no a solicitud ni a productividad diaria.

### Resumen y barras

| Elemento | Cómo interpretarlo |
| --- | --- |
| Expedientes vigentes | Ciclos vigentes activos incluidos en la vista. |
| CURP distintas | Personas distintas de esos ciclos; dos legajos de una persona cuentan como una CURP. |
| TIFF activos | Archivos gestionados activos del ciclo vigente; no incluye retirados ni copias de entregas. |
| Páginas registradas | Suma de páginas conocidas de esos TIFF. |
| Etapas del proceso | Por iniciar, digitalización, revisión, corrección, por aprobar y cerrados; cada ciclo pertenece a una de ellas. |
| Cobertura del trabajo | Recepción, responsable, conteo, TIFF y cierre; un mismo ciclo puede cumplir varias. No sumes esos porcentajes. |
| Fuera de Expedientes | Aviso global de elementos de folios activos que aún no tienen ciclo. Está separado de los filtros y del denominador de las barras. |

Cada porcentaje usa como base los expedientes de esa vista. **Ejemplo:** filtras un folio con 10 ciclos vigentes; 6 tienen conteo confirmado y 2 están cerrados. La cobertura de conteo es **60%** y la de cierre **20%**. No significa que el trabajo esté “80% terminado”. Si solo quedan 4 expedientes al aplicar otro filtro, los porcentajes se recalculan con base 4.

Con cero resultados, las tarjetas muestran cero y los porcentajes **Sin base**. No representa 100% de avance. Si una barra no muestra elementos, selecciónala para comprobar su detalle o revisa los filtros.

### Investigar y exportar

Selecciona una barra para ver los expedientes que la componen y abrir su 360. También puedes llegar al gráfico con Tab, recorrerlo con flechas y abrir con Enter. Desplázate verticalmente en Resumen si la ventana es pequeña.

En **Por folio / digitalizador**, elige la agrupación y usa **Ver expedientes del grupo**. En **Todos los indicadores** consulta además hojas físicas, falta de recepción/asignación/conteo, incidencias, observaciones e inventarios registrados como desactualizados. “Observaciones abiertas” cuenta estados Abierta y En corrección; revisa también las resueltas pendientes de validar en 360 antes de aprobar.

**Exportar indicadores** genera una carpeta nueva con `indicadores.csv`, `etapas.csv`, `cobertura.csv`, agrupaciones, `expedientes.csv` y `contexto.json`. Conserva este último: explica fecha, filtros y alcance. Es la vista seleccionada, no todo el historial del sistema.

Las cifras reflejan metadatos registrados; el panel no vuelve a leer todos los TIFF al escribir en un filtro. Para comprobar integridad y vigencia antes de entregar, usa **Validar expediente**. Los números declarados en Excel/CSV históricos no se suman a los TIFF gestionados.

## 21. Kanban y prioridades

Kanban permite localizar los trabajos por su situación operativa. Filtra por folio, personas, custodia, prioridad, validación u observaciones según la pantalla. Haz doble clic para abrir 360 y atender el expediente.

Las columnas se derivan de recepción, etapa y revisión. **Nota / prioridad** permite destacar una urgencia sin falsear su etapa. Cambiar una tarea auxiliar histórica no avanza automáticamente el proceso documental. Para que se refleje un avance, realiza la acción real de conteo, etapa, revisión o aprobación y actualiza la vista.

Ejemplo: si urge un legajo con reescaneo pendiente, registra la prioridad y atiende el reescaneo; no lo muevas a cerrado para retirarlo del tablero.

## 22. Carpetas y reportes históricos

### Carpeta CURP que ya existía

Abre el ciclo correcto y la pestaña **Importar carpeta CURP** de 360. Si no hay folio comprobado, utiliza **Importación y respaldo → Crear ciclo histórico sin folio comprobado**, con CURP y legajo verificados. Esa agrupación técnica no inventa un préstamo físico ni una recepción.

1. Pulsa **1. Analizar carpeta**. Examina el diagnóstico de archivos, páginas, códigos, duplicados e ilegibles. Este paso no cambia la fuente.
2. Si solo quieres dejar constancia, pulsa **2. Registrar análisis**. Los archivos siguen siendo externos: no cuentan como TIFF activos gestionados.
3. Si vas a gestionarlos en el sistema, revisa las confirmaciones y pulsa **2. Adoptar copias / reanudar**. Se crean copias verificadas; conserva el origen.
4. Si la fuente cambió, vuelve a analizarla. Si la adopción se interrumpió, reanuda siguiendo el registro y no borres su estado a mano.
5. Revisa los documentos ya gestionados en Codificación y valida el expediente.

Un TXT puede aparecer en el análisis, pero no se adopta como TIFF. Un contenido idéntico puede necesitar revisión antes de admitir duplicados; la huella de contenido no equivale por sí sola a identidad documental.

### Excel inicial y CSV de reportes TIFF

Son importadores históricos diferentes de la lista diaria por folio. **Importar Excel inicial** se reserva a una base sin trabajos y al formato histórico previsto. **Importar CSV TIFF** incorpora declaraciones de ejecuciones; no copia automáticamente sus imágenes. Consulta el responsable de migración antes de usarlos con un formato desconocido.

En **Reportes TIFF**, abre **Ver 66 campos** y revisa la ruta y el alcance. **Vincular / corregir vínculo** exige identificar ciclo, folio y legajo. Una declaración de CURP completa no se reparte entre legajos por suposición. En 360 puede aparecer **Confirmar vínculo histórico con el maestro**: úsalo con evidencia; conserva los ciclos separados y no fusiona sus documentos.

## 23. Respaldar y recuperar sin perder capturas

**Al terminar una jornada**, en **Importación y respaldo** pulsa **Respaldar base y TIFF**. Espera el mensaje y anota su ruta. Conserva la carpeta completa con manifiesto, base, documentos y reportes; comprueba el respaldo antes de considerarlo recuperable.

El respaldo automático al cerrar y los snapshots previos a ciertas operaciones contienen **solo la base SQLite**. No bastan para recuperar imágenes. El respaldo completo incluye los archivos gestionados y verifica sus referencias. No incluye automáticamente los Excel/CSV externos, la fuente del escáner, carpetas externas solo analizadas, la `.venv` ni respaldos anteriores.

### Verificar un respaldo en Windows

Con el programa cerrado, abre cmd. Cambia la ruta del ejemplo por la carpeta exacta que indicó el sistema:

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\Digitalizacion\main.py" --verificar-respaldo "D:\Resguardos\RESPALDO_COMPLETO"
```

**Resultado esperado:** verificación correcta sin errores de huellas, integridad ni referencias. Si hay `INCOMPLETO.txt` o la verificación falla, no lo uses como respaldo válido; conserva el mensaje y genera otro al resolver el problema. No edites el manifiesto para que pase.

### Probar una restauración

Restaurar crea una **carpeta nueva**; nunca reemplaza el trabajo existente. Este ejemplo debe ajustarlo quien realiza la recuperación, una línea por vez:

```bat
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\Digitalizacion\main.py" --restaurar "D:\Resguardos\RESPALDO_COMPLETO" --destino "C:\PruebasDigitalizacion\restaurada-01"
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\Digitalizacion\main.py" --workspace "C:\PruebasDigitalizacion\restaurada-01" --diagnostico
"C:\Digitalizacion\.venv\Scripts\python.exe" "C:\Digitalizacion\main.py" --workspace "C:\PruebasDigitalizacion\restaurada-01"
```

La carpeta `restaurada-01` no debe existir antes del primer comando. Comprueba allí folios, legajos, conteos, entregas y varias imágenes. La restauración de datos no crea por sí sola una instalación de código ni su entorno Python. Si vas a convertirla en la instalación de trabajo, sigue el traslado controlado de [RESPALDOS.md](RESPALDOS.md).

Si se interrumpe la restauración, se conserva una marca de incompleta; repite en otra carpeta y guarda la evidencia. Si ya hubo capturas después de un respaldo antiguo, conserva ambos estados y pide conciliación antes de elegir dónde continuar. Nunca pongas una base vieja encima de las capturas nuevas. Tampoco sincronices SQLite y TIFF bidireccionalmente entre equipos.

## 24. Practicar en esta laptop Mac cuantas veces necesites

El laboratorio independiente está en `/Users/admin/PruebasDigitalizacionOSX`. Los accesos existentes permiten continuar sus demos o crear otras; no contienen producción Windows. Mantén separadas las carpetas de código y las sesiones. El nombre del acceso indica la versión, y el título de la aplicación confirma cuál abriste.

Para practicar **0.6.2** sin modificar el código de las copias anteriores, extrae el ZIP de esa versión en una carpeta nueva, por ejemplo `/Users/admin/PruebasDigitalizacionOSX/codigo-0.6.2`. Debe contener `main.py`. Desde Terminal, usando el entorno del laboratorio:

```sh
cd "/Users/admin/PruebasDigitalizacionOSX/codigo-0.6.2"
../.venv/bin/python main.py --crear-demo "../sesiones-v06/practica-manual-01"
../.venv/bin/python main.py --workspace "../sesiones-v06/practica-manual-01"
```

El primer comando de Python se usa una vez para crear esa demo. Para continuarla mañana, repite solo el comando `--workspace` desde la misma carpeta de código. Para otra práctica, cambia `practica-manual-01` por `practica-manual-02` en ambos comandos; la carpeta nueva no debe existir. Cierra una demo antes de abrirla con otro acceso.

Esto usa copias ficticias independientes y no actualiza la instalación Windows. Sigue [LAPTOP.md](LAPTOP.md) para otros accesos existentes. Un ensayo en Mac no verifica el teclado, pantalla, bloqueos de archivos o rendimiento del equipo de oficina.

## 25. Problemas habituales y cómo resolverlos

| Problema | Revisa primero | Acción útil |
| --- | --- | --- |
| Importé y no aparece en Expedientes | Folio, legajo y recepción; filtros activos. | Completa el desglose y acepta los físicos cotejados. Usa Ver en Expedientes. |
| La vista previa mezcla columnas | Hoja, fila de encabezado, separador y correspondencia. | Ajusta el mapa y actualiza la vista previa antes de confirmar. |
| Solo tengo RFC | La identidad fuente. | Solicita/coteja la CURP; deja pendiente. No inventes una. |
| Volví a importar y no cambió nada | El mensaje de lote ya importado. | Revisa pendientes; corrige la fuente en una copia y vuelve a previsualizar. |
| No acepta toda la selección | Discrepancias, faltantes, duplicados, estado de custodia. | Acepta solo los cotejados permitidos; resuelve excepciones individualmente. |
| No asigna el folio | Ciclos pendientes o préstamo en devolución. | Asigna individualmente los aceptados abiertos; completa la recepción antes de asignar todo el folio. |
| Un legajo muestra imágenes de otro | CURP, legajo, folio y ciclo del título. | Conserva evidencias; retira/importa mediante las acciones correctas. No muevas carpetas internas a mano. |
| TIFF y páginas tienen totales diferentes | TIFF multipágina y filtros. | Revisa el contador de páginas. Un archivo puede tener varias. |
| No permite organizar o aprobar | Resultado de Validar expediente y última entrega. | Atiende códigos, conteo, reescaneos, integridad y observaciones; prepara otra entrega si cambió el contenido. |
| Corregí pero sigue la observación | Su estado y entrega de respuesta. | Marca Resuelta con la entrega posterior y solicita la validación explícita del revisor. |
| Indicadores aparecen en cero | Filtros compartidos y ámbito visible. | Limpiar, Actualizar y comprobar Folios si hay elementos sin ciclo. |
| El indicador parece antiguo | Se basa en estados/metadatos registrados. | Actualiza y valida el expediente en 360; no es una inspección automática de cada archivo. |
| El papel sigue como prestado tras aprobar | Estado de custodia del folio. | Registra devolución y aceptación física por separado. |
| El programa dice que ya está abierto | Otra ventana/proceso del mismo espacio. | Cierra la otra sesión; pide revisar el proceso si no aparece. No borres el bloqueo por rutina. |
| El respaldo falla por un archivo | Ruta e integridad del archivo citado. | Conserva el error y resuelve la referencia; no omitas ese documento. |
| Se cortó la energía al actualizar | Resguardo y marca pendiente. | Sigue la recuperación de ACTUALIZACION.html; no abras una mezcla de código ni borres las marcas. |

Cuando pidas apoyo, indica **versión**, sistema operativo, acción que realizabas, texto exacto del error y si estabas en demo o producción. Conserva localmente los registros y evita compartir CURP, imágenes o bases reales en canales no autorizados. La bitácora técnica resume cambios del programa; no debe guardar datos personales de los expedientes.

## 26. Rutina sugerida y dónde encontrar más detalle

**Al empezar:** confirma que abriste la instalación correcta, identifica al operador, revisa pendientes del préstamo y del Kanban, y usa los filtros para tu trabajo asignado.

**Antes de entregar:** confirma el conteo, revisa todas las páginas, valida el ciclo, genera la entrega exacta y conserva su manifiesto. Atiende las observaciones con otra versión y evidencia; la aprobación corresponde a la revisión de la última entrega.

**Al terminar:** guarda ediciones pendientes, registra incidencias y custodia realmente ocurridas, genera respaldo completo y verifica su conservación. Cierra la aplicación con su botón de cierre y espera a que termine.

Para administración y desarrollo consulta [Arquitectura y modelo](MODELO_OPERATIVO_V05.md), [contexto actual del proyecto](CONTEXTO_PROYECTO.md), [bitácora acumulada](BITACORA_DESARROLLO.md), [respaldo y restauración](RESPALDOS.md) y [validación de esta entrega](VALIDACION_V062.md). Los documentos que llevan versiones anteriores son antecedentes o ampliaciones puntuales; este manual reúne el uso vigente de 0.6.2.
