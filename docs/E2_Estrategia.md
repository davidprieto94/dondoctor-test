# E2. Estrategia y Producto de Datos

## 1. Definición y Gobierno del Ausentismo

**Definición recomendada:** 
*Ausentismo = (Citas con estado 'NO_ASISTIO') / (Citas Totales Agendadas - Citas Canceladas por el paciente con antelación permitida).*

**Por qué:** 
La definición actual de la Dirección Comercial (12-14%) y de Operaciones (15-17%) discrepan probablemente porque uno incluye las cancelaciones (CAN) como ausentismo y el otro no, o por el tratamiento de citas reagendadas (REP / REAGENDADA). El ausentismo real debe reflejar exclusivamente la "silla vacía" involuntaria: una cita que el médico esperó atender y el paciente no llegó. Si un paciente cancela a tiempo (permitiendo re-agendar a otro), no es ausentismo operativo, es rotación de agenda.

**Gobierno de la definición (Single Source of Truth):**
Para evitar múltiples cifras, la lógica del indicador no debe vivir en el tablero (Power BI / Excel) ni en consultas ad-hoc. Se gobernará mediante:
1. **Capa Semántica Centralizada:** La métrica se calculará como una columna agregada en el Data Warehouse (tabla de hechos de citas) o en el modelo semántico de Fabric. 
2. **Diccionario Analítico:** Publicación de la definición exacta a nivel de metadatos accesible para los usuarios de negocio.
3. **Bloqueo de Lógica Local:** Los analistas se conectarán al dataset certificado en Fabric; no tendrán permisos para alterar la fórmula de ausentismo en sus reportes individuales.

## 2. Evaluación de Servicios Propuestos por Comercial

Comercial propone dos servicios: a) Benchmark entre IPS, b) Informe mensual a EPS con pacientes de alto riesgo.

### A. Benchmark de Ausentismo (Dashboards para IPS)
* **Recomendación:** Lanzar.
* **Análisis de Valor:** Fomenta la retención de clientes B2B (las IPS) al ofrecerles analítica comparativa de mercado. Es un diferencial competitivo para DonDoctor.
* **Riesgo Legal / Ético (Bajo):** Siempre que los datos del benchmark estén estrictamente **anonimizados y agregados**. Ninguna IPS debe poder deducir el volumen de negocio o la identidad de otra IPS competidora. Las políticas de Tenant Isolation en la arquitectura son vitales aquí.

### B. Informe Mensual a EPS (Listado de afiliados con alto riesgo de inasistencia)
* **Recomendación:** No lanzar en su forma actual, requiere rediseño profundo.
* **Análisis de Valor:** Alto interés de las EPS por intervenir pacientes costosos, pero con un enfoque defectuoso.
* **Riesgo Legal (Alto):** Entregar listados directos de riesgo de pacientes sin su consentimiento explícito para perfilamiento algorítmico viola el Habeas Data y directrices de protección de datos sensibles en salud.
* **Riesgo Ético (Alto):** Perfilar a un paciente como "alto riesgo de inasistencia" y compartirlo con su EPS (aseguradora) puede llevar a discriminación pasiva (ej. la EPS le pone trabas para agendar futuras citas, perjudicando su acceso a la salud).
* **Alternativa de Rediseño:** En lugar de vender el listado a la EPS, DonDoctor debe vender la **intervención**. El servicio sería: "DonDoctor gestiona proactivamente (vía call center / WhatsApp) a los pacientes de la EPS que nuestro modelo identifica en riesgo, para asegurar que asistan o cancelen a tiempo". Mantenemos el control del dato y generamos valor real sin vulnerar al paciente.

## 3. Priorización de Producto de Datos

**Producto priorizado:** Tablero Operativo de Ausentismo y Alertas de Gestión (para la Dirección de Operaciones).

**Por qué:** Antes de monetizar con terceros (EPS), debemos arreglar la casa y dar visibilidad a la operación interna, enfocándonos en la IPS Sur que presenta peores indicadores empíricos.

**Cómo validar disposición de pago / adopción antes de construir:**
* **Prototipado rápido (Mago de Oz):** Enviar durante dos semanas un Excel diario automatizado a Operaciones simulando el tablero final, y medir si realmente lo abren, toman decisiones con él (ej. sobre-agendar ciertos bloques) y si el ausentismo de Sur mejora. Si no hay acción, un tablero interactivo más caro tampoco servirá.

**Medición de Éxito:** 
1. Reducción porcentual del ausentismo real en la IPS Sur (métrica de negocio).
2. MAU (Usuarios Activos Mensuales) del tablero por parte del equipo de Operaciones (métrica de adopción).

## 4. Respuesta a "Tiempo Real"

A la Gerencia General: *El tiempo real en analítica de citas no es necesario ni costo-eficiente.* 
Las citas se agendan con días o semanas de anticipación. Un modelo que prediga la inasistencia 5 minutos antes de la cita no permite ninguna acción (la silla ya quedó vacía). Para poder intervenir un paciente (llamarle, ofrecer reagendamiento, o asignar su espacio a alguien en lista de espera), Operaciones necesita la predicción con **24 a 48 horas de anticipación**. 
Por lo tanto, propondremos una arquitectura de procesamiento **Batch (diario) o Micro-batch (cada 6 horas)**, reduciendo los costos de infraestructura (streaming) en un 80% y cumpliendo con el verdadero caso de uso.

## 5. Hoja de Ruta (90 Días)

| Mes | Entregables (Outputs) | Indicadores de Negocio (Outcomes) |
|---|---|---|
| **Mes 1: Cimientos y Visibilidad** | - Pipeline automatizado (diario) de las 3 IPS piloto en la Capa Limpia de Fabric.<br>- Tablero de Ausentismo v1 (histórico) con la métrica unificada gobernada. | - Disminución a cero en las discrepancias de reportes de ausentismo entre gerencias.<br>- Adopción del tablero por el equipo de Operaciones (>80% de uso semanal). |
| **Mes 2: Intervención Piloto** | - Modelo predictivo v1 desplegado para inferencia Batch (48h antes de la cita).<br>- Integración del output del modelo a listas de trabajo del Contact Center para IPS Sur. | - Aumento del % de confirmaciones o cancelaciones tempranas en IPS Sur en un 15%.<br>- Reducción de la "silla vacía" en un 5% en la IPS Sur. |
| **Mes 3: Monetización Segura** | - Tablero Benchmark de Ausentismo agregado y anonimizado para IPS.<br>- Diseño comercial validado para el servicio de "Gestión Proactiva de Riesgo" hacia las EPS. | - Firma de acuerdos piloto con al menos 2 IPS para el servicio de Benchmark.<br>- Interés validado de 1 EPS por el servicio de gestión proactiva. |
