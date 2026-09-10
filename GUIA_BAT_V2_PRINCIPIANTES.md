# Guía sencilla del BAT v2 para organización de TIFF por CURP

## 1. Qué problema resuelve esta versión

La versión anterior ya hacía una parte importante del trabajo: pedía una CURP, creaba las carpetas `PERSONALES` y `FEDERAL`, identificaba los TIFF por prefijo y los movía al lugar correspondiente.

La versión 2 conserva esas reglas y agrega controles que sirven tanto al digitalizador como al responsable del área.

Reglas conservadas:

- `DP-*.tif` y `DP-*.tiff` → `PERSONALES`
- `FP-*.tif` y `FP-*.tiff` → `PERSONALES`
- `HL-*.tif` y `HL-*.tiff` → `FEDERAL`

No se cambió esta clasificación porque es la regla operativa que ya utiliza el BAT actual.

---

## 2. La idea más importante: no confundir hojas, páginas y archivos TIFF

En el proceso existen al menos tres cantidades distintas:

1. **Hojas físicas**: papel real dentro del expediente.
2. **Páginas digitales**: caras que quedaron digitalizadas dentro de los TIFF.
3. **Archivos TIFF o “digitales”**: cantidad de archivos `.tif`/`.tiff` que hay dentro de la carpeta CURP.

Ejemplo:

- 10 hojas físicas.
- Una hoja tiene información por ambos lados.
- Podrían resultar 11 páginas digitales.
- Dependiendo de la modalidad del escáner, podrían existir 10 TIFF, 1 TIFF, u otra combinación.

Por eso el BAT v2 **no usa el número de páginas para decidir si un documento es INDIVIDUAL o MULTI**.

---

## 3. Por qué el BAT no puede descubrir automáticamente INDIVIDUAL y MULTI

El TIFF por sí mismo no siempre permite conocer la modalidad de trabajo usada por el digitalizador.

Un ejemplo importante es METLIFE:

- Puede procesarse como documento individual.
- Puede generar un TIFF con dos páginas por tratarse de una hoja a doble cara.
- Si el programa dijera “más de una página = MULTI”, lo clasificaría incorrectamente.

Por eso la versión 2 hace algo más seguro:

- Cuenta automáticamente todos los TIFF reales.
- Pregunta cuántos de esos TIFF corresponden a modalidad `MULTI`.
- Calcula:

```text
INDIVIDUALES = TOTAL DE TIFF - MULTI
```

Esta captura manual es una solución temporal. El sistema futuro debe registrar la modalidad desde el momento en que el digitalizador identifica o crea el documento.

---

## 4. Qué pide ahora el BAT

Al ejecutarlo pregunta:

### CURP

La utiliza como identificador del expediente y para crear la carpeta.

Comprueba:

- que tenga exactamente 18 caracteres;
- que solamente contenga letras y números.

### Digitalizador

Pide nombre o identificador de la persona que está trabajando el expediente.

Si se deja vacío, intenta utilizar el usuario de Windows (`%USERNAME%`).

### Hojas físicas

Permite capturar el conteo físico que previamente hizo el digitalizador.

Si no se desea registrar en ese momento, se puede presionar `Enter` y quedará como:

```text
NO_CAPTURADO
```

### Cantidad MULTI

Después de organizar los archivos, el BAT ya sabe cuántos TIFF existen realmente dentro de la carpeta CURP.

Entonces pregunta cuántos corresponden a documentos MULTI.

Ejemplo:

```text
Total TIFF = 9
MULTI = 3
INDIVIDUALES = 6
```

---

## 5. Qué cuenta automáticamente

El BAT calcula el estado final real de la carpeta CURP, no solamente los archivos que movió durante esa ejecución.

Cuenta:

- total de TIFF en `PERSONALES`;
- total de TIFF en `FEDERAL`;
- total general de digitales;
- cantidad `DP-`;
- cantidad `FP-`;
- cantidad `HL-`;
- archivos movidos en esa ejecución;
- conflictos;
- errores de movimiento;
- TIFF que quedaron sueltos en `escaner`;
- TIFF que aparecieron dentro de la CURP pero no corresponden a `DP-`, `FP-` o `HL-`.

Esto es mejor que limitarse a decir “moví 9 archivos”, porque si la carpeta CURP ya contenía algo de una ejecución anterior, el BAT muestra el **total final existente**.

---

## 6. Qué significa RESULTADO

El BAT maneja un resultado de organización, no un estatus oficial del expediente.

### `OK`

No detectó automáticamente:

- conflictos;
- errores de movimiento;
- TIFF sueltos;
- TIFF inesperados dentro de la CURP.

### `REVISAR`

Existe al menos una alerta automática.

### `SIN_DIGITALES`

No existen TIFF dentro de la estructura final.

Muy importante: `OK` **no significa que el expediente ya esté validado por el responsable del área**. Solamente significa que el organizador no detectó problemas dentro de lo que puede comprobar automáticamente.

---

## 7. Qué archivos de control genera

Dentro de la carpeta CURP crea:

### `RESUMEN_DIGITALIZACION.txt`

Resumen fácil de leer para una persona.

Incluye:

- CURP;
- fecha y hora;
- digitalizador;
- hojas físicas;
- digitales;
- individuales;
- multi;
- conteos por carpeta;
- conteos por prefijo;
- conflictos y errores;
- resultado.

También muestra un texto sugerido para copiar al folder físico:

```text
Digitales 9, Fecha 06/09/2026, Digitalizador: Victor
```

### `RESUMEN_DIGITALIZACION.csv`

Contiene el mismo resumen en formato tabular separado por punto y coma.

Esto facilita abrirlo en Excel y posteriormente importar datos al sistema.

### `HISTORIAL_ORGANIZACION.log`

Cada vez que el BAT se vuelve a ejecutar sobre la misma CURP agrega una línea al historial. Así una nueva ejecución no borra completamente la evidencia de que hubo una ejecución anterior.

---

## 8. Control acumulado de varias CURP

En la carpeta `escaner`, el BAT crea:

```text
CONTROL_DIGITALIZACION.csv
```

Cada ejecución agrega una fila.

Ejemplo conceptual:

| CURP | Digitalizador | Físicos | Digitales | Individuales | Multi | Resultado |
|---|---|---:|---:|---:|---:|---|
| CURP-1 | Victor | 156 | 9 | 6 | 3 | OK |
| CURP-2 | Victor | 87 | 12 | 10 | 2 | REVISAR |

Esto puede ayudar temporalmente al encargado a realizar sumatorias de varias carpetas sin abrir cada CURP y contar manualmente los TIFF.

No sustituye al futuro sistema; es una solución intermedia.

---

## 9. Qué pasa si la carpeta CURP ya tenía archivos

La versión 2 avisa:

```text
AVISO: La carpeta CURP ya contenía archivos TIFF.
```

El resumen final cuenta el total acumulado real que existe en ese momento.

Esto es importante porque el número “movidos en esta ejecución” y el número “total digitales” pueden ser diferentes.

Ejemplo:

```text
Ya existían: 5
Movidos ahora: 3
Total digitales final: 8
```

---

## 10. Conflictos

Si ya existe en el destino un TIFF con el mismo nombre, el BAT no lo reemplaza.

Ejemplo:

```text
escaner\DP-01.tif
CURP\PERSONALES\DP-01.tif
```

El resultado será un conflicto y el archivo de `escaner` permanecerá ahí para revisión humana.

Esta decisión es intencional: es más seguro detener y revisar que reemplazar silenciosamente documentación digitalizada.

---

## 11. Qué mejoras NO se hicieron todavía

### No se identifica automáticamente el tipo documental leyendo la imagen

El BAT solamente entiende el prefijo del nombre:

```text
DP-
FP-
HL-
```

No hace OCR ni analiza visualmente el TIFF.

### No se implementó un catálogo de incidencias dentro del BAT

El catálogo todavía se está definiendo. Codificar una lista provisional dentro del BAT podría convertir errores temporales en reglas permanentes.

El sistema futuro sí debe tener un catálogo editable, versionado y auditable.

### No marca el expediente como “validado”

El responsable del área todavía debe validar el trabajo del digitalizador.

### No modifica ni elimina páginas

El BAT no intenta detectar “páginas en blanco” ni eliminar reversos. Esto es especialmente importante porque en los expedientes pueden existir hojas recicladas, información rayada o caras que visualmente parezcan poco relevantes pero forman parte del documento físico recibido.

---

## 12. Cómo mejora el trabajo del responsable

Antes, para validar varias CURP, el encargado podía necesitar:

1. abrir cada carpeta;
2. contar archivos;
3. sumar manualmente;
4. comparar contra Excel.

Ahora el BAT deja dos niveles de resumen:

```text
CURP\RESUMEN_DIGITALIZACION.csv
```

para una CURP, y:

```text
escaner\CONTROL_DIGITALIZACION.csv
```

para varias ejecuciones.

Esto permite comprobar más rápido diferencias entre lo capturado y lo que realmente existe en disco.

---

## 13. Cómo debe evolucionar esto en el sistema

El BAT es un puente, no el sistema final.

El futuro sistema debería hacer automáticamente:

```text
Recepción del lote
        ↓
Importación del Excel oficial
        ↓
Validación expediente físico ↔ datos oficiales
        ↓
Asignación a digitalizador
        ↓
Conteo físico
        ↓
Registro de incidencias
        ↓
Digitalización
        ↓
Registro de modalidad INDIVIDUAL / MULTI / otras
        ↓
Clasificación documental DP / FP / HL / catálogo futuro
        ↓
Conteo automático de TIFF
        ↓
Conciliación con datos capturados
        ↓
Cierre por digitalizador
        ↓
Revisión del responsable
        ↓
Validación / observación / corrección
        ↓
Cierre final con bitácora
```

El principio más importante será que **cada cantidad tenga un significado único** y que toda modificación importante deje trazabilidad de quién, cuándo y por qué la realizó.

---

## 14. Cómo usar el BAT v2

1. Haz una copia de seguridad de tus TIFF de prueba.
2. Coloca el BAT dentro de la carpeta `escaner`.
3. Empieza con un expediente de prueba, no con producción.
4. Ejecuta el BAT.
5. Captura CURP, digitalizador y físicos.
6. Revisa los movimientos que muestra en pantalla.
7. Captura la cantidad total de TIFF que corresponden a MULTI.
8. Revisa el resumen.
9. Abre la carpeta CURP y confirma visualmente la estructura.
10. Abre `RESUMEN_DIGITALIZACION.txt` y `RESUMEN_DIGITALIZACION.csv`.
11. Compara contra tu conteo manual antes de utilizarlo con expedientes reales.

---

## 15. Regla de seguridad para esta etapa

Mientras el proceso todavía se está aprendiendo y estandarizando:

> El programa debe automatizar primero lo que puede comprobar con certeza y dejar como decisión humana explícita aquello que todavía depende del criterio documental del digitalizador.

Esa es la razón por la que esta versión automatiza conteos y conciliaciones simples, pero no pretende decidir todavía qué contiene una imagen TIFF.
