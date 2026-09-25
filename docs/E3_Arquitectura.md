# E3. Arquitectura Objetivo en Azure y Microsoft Fabric

## 1. Diagrama de Arquitectura

![Diagrama de Arquitectura](img/arquitectura.png)

## 2. Documento de Decisiones Arquitectónicas

### A. Ingesta sin afectar la operación
Para garantizar que las cargas analíticas no degraden el rendimiento de los sistemas transaccionales de las IPS (OLTP), definimos los siguientes patrones:
* **SQL Server (IPS Norte, Sur, Occidente):** Se implementará un patrón de **Ingesta Incremental (Change Data Capture - CDC)** soportado nativamente en Azure Data Factory / Fabric Pipelines. De no ser posible activar CDC en la fuente por políticas del cliente, se implementará una ingesta por marca de agua (Watermarking) basada en la columna de auditoría `fecha_actualizacion`. Las extracciones (`Extracciones` en el diagrama) se programarán en ventanas de mantenimiento nocturnas o de bajo tráfico.
* **MongoDB (Eventos WhatsApp):** Se utilizará el conector nativo de Fabric Data Factory hacia MongoDB. Para asegurar que no haya bloqueos (locks) de lectura/escritura en la base de datos principal, la conexión apuntará estrictamente a un **nodo secundario (réplica de lectura)** del clúster de MongoDB.

### B. Organización por capas y Modelo Canónico Multi-cliente
Implementamos una **Arquitectura Medallón sobre OneLake (Formato Delta Parquet)**, orquestada mediante Fabric Pipelines y separada lógicamente por Workspaces según entornos (`{ENV}`: DEV, QA, PRD) y dominios de negocio (`{DOMINIO NEGOCIO}` y `{DOMINIO DATO}`).

1. **Capa Bronze (`lh_brz_<d_neg>_<d_dat>`):** 
   - Alojada en el Lakehouse de Bronze.
   - Naturaleza *Append-Only*. Los datos de cada cliente aterrizan en bruto, manteniendo el 100% de la fidelidad del esquema original (ej. `id_cita` para Occidente, `cita_id` para Norte).
2. **Capa Silver (`lh_slv_<d_neg>_<d_dat>`):** 
   - Procesamiento mediante Notebooks de Spark en Fabric.
   - Aquí reside el **Modelo Canónico**. El código Spark aplica diccionarios de homologación dinámicos para estandarizar los esquemas dispares de las IPS hacia una estructura unificada de citas.
   - Se ejecutan rutinas de deduplicación y resolución de tipos de datos.
3. **Capa Gold (`dw_gld_<d_neg>_<d_dat>`):** 
   - Alojada en un Workspace separado (`-gld`) para aislar los cómputos de consumo.
   - Modelado Dimensional (Kimball): Tablas de Hechos (Fact_Citas) y Dimensiones (Dim_Pacientes, Dim_IPS). 
   - Optimizado para consultas interactivas mediante el SQL Endpoint de Fabric.

### C. Visibilidad, Gobierno y Seguridad de PII
El gobierno de datos es transversal a la plataforma, soportado por la suite de Microsoft:
* **Seguridad de Acceso (Microsoft Entra ID):** Control de acceso basado en roles (RBAC) a nivel de Workspace.
* **Gobierno y Linaje (Microsoft Purview):** Clasificación automática de datos sensibles y trazabilidad de linaje desde SQL Server hasta Power BI.
* **Gestión de Secretos (Azure Key Vault):** Las cadenas de conexión a las IPS nunca residen en código; se consumen dinámicamente desde el Key Vault.
* **Enmascaramiento de PII:** En el paso de Bronze a Silver, columnas sensibles (como `documento_identidad` y `telefono`) sufren un Hashing unidireccional (SHA-256) con un *salt* resguardado en Key Vault.
* **Row-Level Security (RLS) Multi-tenant:** En la capa Gold y Power BI, implementamos políticas RLS basadas en la identidad del usuario (Entra ID) mapeada a la dimensión de IPS, asegurando que un gerente de la IPS Sur no pueda consultar registros de la IPS Norte.

### D. Estimación de Capacidad, Costos y Manejo de Cargas Pesadas
* **Supuestos:** Aunque el piloto maneja decenas de miles de registros, la arquitectura está diseñada para escalar a cientos de IPS (millones de registros diarios).
* **Capacidad Fabric (SKUs F):** Para el arranque, proponemos un SKU F2 o F8 (pago por uso / reserva), oscilando entre $250 y $1,000 USD mensuales, lo cual incluye cómputo de Spark, Data Factory y Power BI Premium.
* **Aislamiento de Cargas (Workload Isolation):** Uno de los mayores riesgos es que un modelo de Machine Learning consuma toda la capacidad, tumbando los tableros gerenciales. Lo evitamos de dos formas:
   1. **Workspaces separados:** La capa Gold (consumo) vive en su propio Workspace.
   2. **Separación de Cómputo (OneLake):** Los ingenieros y científicos de datos leen los datos delta directamente de OneLake mediante los Spark Pools (para entrenamiento), sin tocar el SQL Endpoint que Power BI usa para servir los dashboards.

### E. Ambientes de Desarrollo, Pruebas y Producción
Adoptamos un enfoque estricto de CI/CD:
* Los nombres de los Workspaces incluyen el sufijo `{ENV}` (DEV, QA, PRD).
* Todo el código (Notebooks, Pipelines, SQL) se versiona en **Azure DevOps**.
* Los despliegues entre entornos se realizan mediante los *Deployment Pipelines* de Fabric.
* El entorno de DEV opera sobre datos sintéticos o un subconjunto altamente ofuscado; los desarrolladores jamás tocan datos reales de producción (PRD).

### F. Consumo de Modelos de IA de forma Trazable (Azure Machine Learning)
Para habilitar modelos predictivos (ej. predicción de ausentismo), la arquitectura se extiende hacia servicios especializados:
* **Entrenamiento:** Los científicos de datos utilizan **Azure Machine Learning (AML)** conectado nativamente a los datos de la capa Gold en OneLake (vía atajos/shortcuts). Esto permite entrenar modelos (XGBoost, Random Forest) con un seguimiento estricto de experimentos y registro de modelos en el *Model Registry* de AML.
* **Inferencia y Despliegue:** El modelo entrenado se expone como un **Managed Endpoint** en Azure ML.
* **Consumo Trazable:** Fabric Data Factory consume este endpoint mediante llamadas batch, inyectando la probabilidad de inasistencia en una nueva Fact Table (`Fact_Predicciones`) en la capa Gold, permitiendo cruzar la predicción vs la realidad en Power BI.
* **Visión a Futuro (Azure AI Foundry):** En una fase 2, integraremos **Azure AI Foundry** para evolucionar de la analítica predictiva a la Inteligencia Artificial Generativa. Mediante agentes conversacionales RAG (Retrieval-Augmented Generation) conectados al modelo semántico de Fabric, permitiremos que las IPS consulten su ausentismo interactuando en lenguaje natural ("¿Cuál fue mi tasa de inasistencia la semana pasada?"), manteniendo siempre las políticas de RLS.

### G. Qué NO haríamos en Fabric y por qué
**No usaríamos Fabric como base de datos transaccional (OLTP) ni como backend para la aplicación de agendamiento en tiempo real.**
* **Por qué:** Microsoft Fabric (y OneLake con su formato Parquet/Delta) está diseñado nativamente para cargas de trabajo analíticas (OLAP). Intentar que la aplicación de DonDoctor o su bot de WhatsApp inserte o actualice citas una a una directamente en Fabric con latencia de milisegundos sería un desastre arquitectónico, degradando el rendimiento y disparando los costos. Los sistemas transaccionales (SQL Server/Mongo) son los dueños de la operación; Fabric es el cerebro para analizarla.
