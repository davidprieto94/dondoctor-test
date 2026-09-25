# E5. Modelo Predictivo

El código fuente (reproducible) de esta solución está implementado en Python y se encuentra en [`src/model.py`](../src/model.py). Se eligió un script automatizado en lugar de un *Jupyter Notebook* para demostrar estándares de producción (*Production-Ready Machine Learning*).

A continuación, se responden los requerimientos estratégicos del modelo:

## 1. Decisión de negocio y momento exacto de la predicción
* **Decisión que habilita:** El modelo habilita la decisión de **"Intervención Proactiva"** (agendamiento de llamadas desde el Call Center o envío de WhatsApps prioritarios con posibilidad de cancelación y reasignación de citas a pacientes en lista de espera).
* **Momento exacto de la predicción:** El modelo debe ejecutarse de forma *batch* todas las madrugadas (ej. 2:00 AM) operando sobre las citas que están programadas para **dentro de 48 horas exactas**. Esto otorga al Call Center una ventana de 2 días útiles para llamar al paciente en alto riesgo, confirmar su asistencia o liberar su silla.

## 2. Definición de la Variable Objetivo (Target) y Features
* **Variable Objetivo (`Target`):** Variable binaria donde `1` significa que el paciente NO ASISTIÓ ("NO_ASISTIO") y `0` significa que SÍ asistió ("ATENDIDA"). Se filtran y omiten registros de citas canceladas a tiempo, ya que no constituyen ausentismo operativo.
* **Justificación de Variables Incluidas:**
  * `Lead_Time` (Días entre fecha de creación y fecha de cita): *Feature* crucial. A mayor tiempo de espera, mayor probabilidad de olvido de la cita.
  * `Hora_del_dia`: Captura patrones de tráfico u horarios laborales que impiden la asistencia (ej. inasistencias más frecuentes a las 3:00 PM).
  * `Regimen`: El tipo de régimen de salud impacta por las barreras sistémicas (transporte, permisos laborales) asociadas a poblaciones de distintas capacidades económicas.
* **Variables Descartadas:**
  * `Documento` y `Nombre`: Eliminados por no aportar varianza predictiva y para proteger la PII (evitar sobreajuste hacia individuos particulares).
  * `Id_Cita`: Descartada al ser un identificador único aleatorio.

## 3. Modelo Base Simple vs. Elaborado
* **Modelo Base (Baseline):** Se entrenó una **Regresión Logística**. Es altamente interpretable, rápida de entrenar y sirve como punto de partida para entender qué coeficientes (ej. `Lead_Time`) tienen mayor impacto lineal.
* **Modelo Elaborado:** Se entrenó un **Random Forest Classifier**. Este modelo de ensamble captura interacciones no lineales complejas (ej. "Pacientes de régimen subsidiado con más de 20 días de lead time"). En producción, este modelo entrega mejor poder de generalización para la clasificación.

## 4. Estrategia de Validación
Se aplicó una validación **Hold-Out (Train-Test Split)** del 70/30 estratificada (manteniendo la misma proporción de ausentismo en ambos conjuntos). Dado que es un modelo transversal sobre el tiempo, en el entorno de producción se recomienda reemplazar esto por una validación de ventana rodante temporal (*Time-Series Split* u *Out-Of-Time Validation*) para asegurar que predecimos el futuro utilizando estrictamente datos del pasado sin *data leakage*.

## 5. Métrica Principal
La métrica principal optimizada y reportada es el **Recall (Sensibilidad)** de la clase minoritaria (Ausentismo = 1).
* **Justificación:** Confiamos en esta métrica porque el costo de los "Falsos Negativos" (un paciente que falta, pero el modelo predijo que iba a asistir) es altísimo (una silla vacía = pérdida financiera para la IPS). Preferimos asumir algunos "Falsos Positivos" (llamar a un paciente que sí iba a ir) ya que una llamada de cortesía aporta valor al servicio al cliente y no tiene un costo prohibitivo.

## 6. Análisis de Comportamiento (Sesgos) e Implicación Responsable
El código evalúa el desempeño del modelo desglosado por grupos, específicamente por `Régimen`. 
* **Hallazgo (Simulado):** Es estadísticamente probable que el modelo asigne *scores* de riesgo mucho más altos a la población de régimen *Subsidiado* debido a barreras sistémicas del sistema de salud. 
* **Implicación Ética:** Si el modelo se usa de forma automática para cancelar citas de alto riesgo sin intervención humana, estaríamos castigando y discriminando sistemáticamente a la población más vulnerable, violando principios de IA Responsable.

## 7. Recomendación Final
* **Para qué SÍ usarlo:** Usar el modelo como una **herramienta de triaje priorizado**. Los *scores* más altos de riesgo deben dirigir los recursos limitados del Call Center para hacer llamadas amables de recordatorio o ayudar al paciente a resolver dudas o re-agendar, mejorando su experiencia.
* **Para qué NO usarlo:** Prohibido usar este modelo para **castigar pacientes** (ej. aplicar multas, cobrar "no-show fees", poner en listas negras) o para vender listados nominales de "malos pacientes" a entidades externas (EPS o aseguradoras) por fines netamente comerciales.
