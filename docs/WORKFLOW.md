# Flujo operativo y estados

## Recorrido

```text
RECEIVED → ASSIGNED → IN_PROGRESS → READY_FOR_REVIEW
                                            |          |
                                            |          +→ VALIDATED → CLOSED
                                            +→ OBSERVED → CORRECTED
                                                              |       |
                                                              +→ OBSERVED
                                                                      o VALIDATED
```

`CANCELLED` exige permiso y motivo y solo se admite antes de validar. Su operación normal queda pendiente de la política del área.

## Reglas aplicadas

- Solo un responsable con capacidad de asignación cambia la custodia.
- Una reasignación cierra la asignación anterior; no la reemplaza.
- El digitalizador confirma la recepción y correspondencia físico/digital antes de poder iniciar; fecha y notas quedan en la asignación y en auditoría.
- Solo el digitalizador actualmente asignado puede iniciar, terminar o enviar correcciones.
- Iniciar crea una `ScanSession`; terminar cierra la sesión activa.
- Terminar produce `READY_FOR_REVIEW`, nunca `VALIDATED`.
- Observar requiere texto y crea un `QualityReview` histórico.
- El digitalizador responde a una observación con `CORRECTED`.
- Revisores/responsables pueden observar de nuevo o validar una corrección.
- En el MVP nadie puede revisar su propio trabajo, aunque pertenezca a ambos grupos.
- Validar y cerrar son acciones separadas.
- Toda transición crea `RecordStatusTransition` y `AuditEvent`.

## Controles no convertidos en reglas

Una incidencia marcada `blocks_flow` se muestra como alerta, pero todavía no bloquea una transición porque las fuentes no indican en qué etapa debe hacerlo. Tampoco se exige un conjunto inventado de conteos para enviar o validar. Estas políticas están en `OPEN_QUESTIONS.md`.
