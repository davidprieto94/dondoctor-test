# E1. Diagnóstico y Calidad de Datos

Este documento resume los hallazgos del análisis exploratorio realizado sobre las fuentes de datos piloto (tres bases de datos transaccionales de citas y una colección de eventos de mensajería).

## 1. Perfilamiento General
* **IPS Norte (`ips_norte_citas.csv`)**: 6,555 registros. Formato CSV estándar (separado por comas). 
* **IPS Sur (`ips_sur_citas.csv`)**: 5,312 registros. Formato CSV estándar. 
* **IPS Occidente (`ips_occidente_citas.csv`)**: 4,228 registros. **Usa punto y coma (`;`) como separador.**
* **WhatsApp (`whatsapp_eventos.jsonl`)**: 38,416 eventos JSON.

## 2. Hallazgos y Evidencia Cuantitativa

### H1. Exposición de Datos Sensibles (PII) no documentados
* **Evidencia**: La base de IPS Sur contiene las columnas `documento_identidad` y `telefono`, las cuales no están estipuladas en el diccionario de datos.
* **Código de respaldo**: Validación programática en [`src/eda.py`](file:///c:/Users/david/Documents/dondoctor/src/eda.py#L21-L22) (Línea 22).
* **Impacto**: Riesgo legal severo. Se están ingiriendo datos directamente identificables (PII) a un entorno de analítica, violando normativas de protección de datos (Habeas Data).
* **Tratamiento**: Omitir la carga de estas columnas desde la fuente o aplicar una función de *hash* unidireccional en la capa de ingesta cruda.

### H2. Inconsistencia de Esquemas y Dominios (Estados)
* **Evidencia**: IPS Occidente tiene nombres de columnas diferentes (ej. `id_cita` vs `cita_id`) y los estados están abreviados (`ATD`, `CAN`, `NAS`, `REP`, `PEN`, `CONF`). Adicionalmente, IPS Norte contiene un estado `REAGENDADA` (363 registros) que no está definido en el diccionario de datos original.
* **Código de respaldo**: Validación programática en [`src/eda.py`](file:///c:/Users/david/Documents/dondoctor/src/eda.py#L24-L27) (Líneas 25-27) y en [`notebooks/01_E1_diagnostico_datos.ipynb`](file:///c:/Users/david/Documents/dondoctor/notebooks/01_E1_diagnostico_datos.ipynb).
* **Impacto**: Genera errores al intentar consolidar el modelo de datos canónico si no se homologan.
* **Tratamiento**: Crear un diccionario de homologación en la capa *Limpia* (Clean) para mapear columnas y valores de estado al estándar dictado por el diccionario de datos.

### H3. Duplicidad de Registros
* **Evidencia**: La IPS Norte contiene 198 identificadores únicos (`cita_id`) duplicados. Las otras IPS tienen 0 duplicados.
* **Código de respaldo**: Validación programática en [`src/eda.py`](file:///c:/Users/david/Documents/dondoctor/src/eda.py#L29-L31) (Líneas 30-31).
* **Impacto**: Puede inflar artificialmente las métricas de ausentismo y volumen de citas.
* **Tratamiento**: Aplicar una regla de deduplicación basada en `fecha_actualizacion` (quedarse con el registro más reciente).

### H4. Incoherencia Temporal en el Agendamiento
* **Evidencia**: Existen citas donde la `fecha_creacion` (cuando se agendó) es posterior a la `fecha_cita` (cuando ocurre la cita). Encontramos 49 casos en Norte y 34 en Sur.
* **Código de respaldo**: Validación programática en [`src/eda.py`](file:///c:/Users/david/Documents/dondoctor/src/eda.py#L33-L42) (Líneas 35-42).
* **Impacto**: Corrompe modelos predictivos y el cálculo de *lead time* (tiempo de anticipación del agendamiento). 
* **Tratamiento**: Filtrar estos registros y reportarlos en una tabla de auditoría (Dead Letter Queue).

### H5. Eventos Huérfanos de WhatsApp
* **Evidencia**: De los eventos de recordatorio de WhatsApp, existen **12,069 eventos** cuyo identificador (`contexto.ref_cita`) no aparece en ninguna de las tres bases de datos de IPS proporcionadas.
* **Código de respaldo**: Validación programática en [`src/eda.py`](file:///c:/Users/david/Documents/dondoctor/src/eda.py#L44-L48) (Líneas 45-48).
* **Impacto**: Se pierde la trazabilidad de los recordatorios, afectando la evaluación del canal de WhatsApp.
* **Tratamiento**: Ignorar estos eventos en el modelo analítico actual, asumiendo que corresponden a otras IPS no incluidas en este piloto.

---

## 3. Reglas de Calidad a Implementar (Pipeline E4)
Para evitar que estos problemas pasen silenciosamente:
1. **Regla de Esquema**: Fallar la ejecución si se detectan columnas de PII (como `documento` o `telefono`) no enmascaradas en la capa de consumo.
2. **Regla de Unicidad**: Validar que el conteo de `cita_id` sea igual al conteo de valores distintos en la capa Limpia.
3. **Regla de Integridad Lógica**: Lanzar advertencia (warning) si `fecha_creacion > fecha_cita`.
4. **Regla de Dominio**: Verificar que la columna `estado` solo contenga valores estrictamente definidos en la ontología de DonDoctor (PENDIENTE, CONFIRMADA, ATENDIDA, NO_ASISTIO, CANCELADA).

---

## 4. Preguntas al Dueño del Dato (Data Steward)
1. **[Riesgo Legal]** Notamos que la IPS Sur envía `documento_identidad` y `telefono`. ¿Podemos omitir la ingesta de estos campos en la capa cruda, o necesitan que los mantengamos seudonimizados mediante hashing?
2. **[Definición]** Encontramos el estado `REAGENDADA` en Norte y `REP` en Occidente. ¿Este estado cuenta como "ausentismo" o lo tratamos como una cita cancelada a tiempo?
3. **[Integridad]** Hay 12,069 eventos de WhatsApp que no cruzan con ninguna cita. ¿Esto se debe a que pertenecen a otras IPS fuera del piloto, o tenemos un problema de llaves de cruce?
4. **[Calidad]** Existen citas donde la fecha de creación es posterior a la cita. ¿Es posible que sean citas agendadas retrospectivamente para registrar urgencias (walk-ins)?
5. **[Calidad]** Encontramos 198 registros con `cita_id` duplicado en Norte. ¿Podemos asumir que el registro válido es el que tiene la `fecha_actualizacion` más reciente?
6. **[Esquema]** ¿Existe un plan a corto plazo para que Occidente cambie su delimitador a coma y unifique los nombres de sus columnas, o el pipeline debe soportar estos formatos de forma indefinida?
