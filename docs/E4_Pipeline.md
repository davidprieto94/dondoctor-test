# E4. Pipeline de Datos Implementado

El código fuente del pipeline se encuentra en el archivo [`src/pipeline.py`](../src/pipeline.py). 

A continuación, se responden los lineamientos requeridos por la prueba:

## 1. Pasos aplicados para la limpieza y su necesidad
El pipeline ejecuta secuencialmente los siguientes pasos críticos en la capa "Clean":
* **Enmascaramiento de PII (Hashing):** La IPS Sur enviaba la `cédula` y el `teléfono` (datos sensibles). Se aplicó un Hash SHA-256 unidireccional. Esto es necesario por Seguridad por Diseño, garantizando que ninguna tabla en la capa de consumo exponga identidad directa de pacientes, cumpliendo con leyes de Habeas Data, mientras se preserva la integridad referencial.
* **Conversión y Tipado de Fechas:** Las fechas venían como *strings* o en formatos inconsistentes. Se estandarizaron usando `pd.to_datetime`. Necesario para poder calcular diferencias temporales precisas (como el *Lead Time* o días de anticipación de cita).
* **Deduplicación:** Se identificaron registros duplicados por `cita_id` (especialmente en la IPS Norte). Se eliminaron reteniendo solo la última versión (`keep='last'`) basada en la fecha de actualización, lo cual es vital para no inflar las métricas de volumen de pacientes y tasas de inasistencia.
* **Manejo de Valores Nulos:** Se aplicó imputación básica en variables continuas y categóricas para evitar que el modelo predictivo posterior (E5) falle por *missing values*.

## 2. Resolución de inconsistencia de esquemas
Las tres IPS tenían formatos dispares. La resolución se abordó mediante la construcción de un **Modelo Canónico** en la capa "Clean":
* **Homologación de Columnas:** IPS Occidente tenía `id_cita`, mientras las demás tenían `cita_id`. Se utilizó el método `rename` de Pandas aplicando un diccionario estático para unificar los nombres de las columnas antes de concatenar los DataFrames.
* **Homologación de Dominios (Estados):** IPS Occidente utilizaba abreviaturas (`ATD`, `CAN`, `NAS`) e IPS Norte introdujo estados no documentados (`REAGENDADA`). Se aplicó un diccionario de mapeo maestro (ej. `'REAGENDADA': 'CANCELADA'`, `'NAS': 'NO_ASISTIO'`) garantizando que la tabla consolidada final solo tenga los 4 estados canónicos permitidos por el negocio.
* **Estandarización de Separadores:** El pipeline fue diseñado para ingerir de forma flexible archivos con separadores de coma `,` y punto y coma `;` (caso Occidente) gestionándolo dinámicamente en el método de lectura `pd.read_csv()`.

## 3. Estrategia de llave de cruce (Join Key) con MongoDB (Eventos WhatsApp)
Para enlazar el JSON de eventos de WhatsApp con el modelo relacional de citas, la estrategia implementada fue:
1. **Extracción y Aplanamiento (Flattening):** Usando `json_normalize`, se aplanó la estructura anidada del JSON para extraer el campo profundo `contexto.ref_cita`.
2. **Casteo de Llaves:** Se aseguró que tanto `contexto.ref_cita` en los eventos como `cita_id` en las transacciones estuvieran en formato `string` puro (sin decimales ni notación científica) para evitar falsos negativos en los cruces.
3. **Cruce (Left Join):** Se propuso una estrategia de `Left Join` desde la tabla consolidada de citas hacia los eventos, utilizando `cita_id = contexto.ref_cita`, para contar cuántos recordatorios tuvo una cita.
*Nota de hallazgo:* Como se evidenció en E1, actualmente hay un desacople operativo: los más de 38,000 eventos de WhatsApp son huérfanos (no hicieron *match* con el piloto actual de citas). La estrategia de código está construida y es robusta, pero la data requiere corrección desde la fuente para que el cruce arroje resultados mayores a cero.
