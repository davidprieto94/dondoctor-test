# E3. Arquitectura Objetivo en Azure y Microsoft Fabric

## 1. Diagrama de Arquitectura

![Diagrama de Arquitectura](img/arquitectura.png)

## 2. Documento de Decisiones Arquitectónicas (ADR)

*Nota de alcance: La presente arquitectura se ha diseñado teniendo en cuenta la premisa de escalabilidad masiva para soportar la futura ingesta de decenas de clínicas e IPS, priorizando el desacoplamiento de cargas, la seguridad de la información sanitaria y la habilitación de capacidades de Inteligencia Artificial avanzadas.*

### A. Estrategia de Ingesta sin impacto operativo (OLTP a OLAP)
El principal riesgo en un entorno clínico es que las consultas analíticas degraden el rendimiento de las bases de datos transaccionales, retrasando procesos críticos como el agendamiento o la atención en ventanilla. Para mitigarlo, la ingesta hacia Microsoft Fabric se realizará bajo los siguientes lineamientos:

1. **Bases de Datos Relacionales (SQL Server - IPS Norte, Sur, Occidente):**
   - **Mecanismo Principal (Change Data Capture - CDC):** Habilitaremos la funcionalidad nativa de CDC en las instancias de SQL Server de las IPS. Fabric Data Factory Pipelines leerá exclusivamente el *Transaction Log* (Log Sequence Numbers - LSN), capturando únicamente los inserts, updates y deletes sin realizar *full table scans*.
   - **Mecanismo de Respaldo (Watermarking):** Si por políticas de infraestructura del cliente no es posible habilitar CDC, implementaremos un patrón de marca de agua utilizando las columnas `fecha_actualizacion` o `timestamp`. 
   - **Frecuencia y Ventanas:** La orquestación de *pipelines* priorizará la ejecución de micro-batches (cada 4-6 horas) y cargas pesadas de recálculo exclusivamente en ventanas nocturnas (01:00 AM - 04:00 AM).

2. **Bases de Datos NoSQL (MongoDB - Eventos WhatsApp):**
   - **Lectura desde Réplicas:** Las conexiones nativas de Fabric Data Factory hacia el clúster de MongoDB se enrutarán obligatoriamente a los nodos secundarios (Réplicas de Lectura). Esto garantiza aislamiento total (cero bloqueos) sobre el nodo primario que atiende las interacciones en vivo con los pacientes vía WhatsApp.

### B. Topología de Workspaces y Modelo Canónico Multi-Cliente (Arquitectura Medallón)
El ecosistema analítico se fundamenta en OneLake (el OneDrive para datos de Fabric) estructurado bajo la Arquitectura Medallón, utilizando el formato abierto **Delta Parquet** para garantizar transacciones ACID y evolución de esquemas (*Schema Evolution*).

1. **Capa Bronze (`lh_brz_<d_neg>_<d_dat>`):** 
   - **Patrón:** *Append-Only* y fidelidad total.
   - **Decisión:** Los datos crudos aterrizan en su estructura nativa. Mantener las columnas originales (ej. `id_cita` para Occidente, `cita_id` para Norte) en esta capa es crucial para propósitos de auditoría y linaje. Nunca mutamos datos en Bronze.

2. **Capa Silver (`lh_slv_<d_neg>_<d_dat>`):** 
   - **Patrón:** Limpieza, filtrado y estandarización (El Modelo Canónico).
   - **Decisión:** Utilizaremos Spark Notebooks (PySpark) para leer la capa Bronze y transformar los distintos diccionarios de datos hacia una única taxonomía unificada (Modelo Canónico). Aquí se resuelven conflictos de zona horaria, se normalizan los estados de las citas (ej. mapeando 'REP' o 'REAGENDADA' al dominio estándar) y se aplican lógicas de deduplicación sobre llaves naturales. El resultado es un *Lakehouse* consolidado donde cada IPS 'habla el mismo idioma'.

3. **Capa Gold (`dw_gld_<d_neg>_<d_dat>`):** 
   - **Patrón:** Consumo analítico (Modelado Dimensional de Kimball).
   - **Decisión:** Alojada en un Workspace dedicado (`-gld`) para aislar los cómputos. Se estructura en Tablas de Hechos granulares (`Fact_Citas`) y Dimensiones conformadas (`Dim_Pacientes`, `Dim_IPS`, `Dim_Calendario`). Power BI se conectará a esta capa utilizando conectividad *Direct Lake*, logrando latencias de milisegundos sin necesidad de importar datos (Import Mode), manteniendo siempre la versión única de la verdad.

### C. Gobierno Transversal, Privacidad y Seguridad (PII)
Operar con datos de pacientes (PHI/PII) exige el nivel más alto de cumplimiento normativo (Habeas Data, HIPAA). La arquitectura incluye una capa superior de "Gobierno, Accesos y Servicios Transversales":

* **Gestión de Identidades y Acceso (Microsoft Entra ID):** Todo acceso a la plataforma se autentica centralizadamente. Se aplicará el principio de mínimo privilegio (PoLP) usando roles nativos de Workspace (Admin, Member, Contributor, Viewer).
* **Auditoría y Linaje (Microsoft Purview):** Se integrará Purview para escanear OneLake automáticamente. Esto habilitará un *Data Catalog* donde las métricas de ausentismo estén documentadas y certificadas, y un mapa de datos (*Data Map*) que trace el viaje del dato desde el SQL Server de la IPS hasta el visual de Power BI.
* **Seguridad de Secretos (Azure Key Vault):** Cero credenciales en código. Los tokens de APIs, contraseñas de bases de datos y llaves criptográficas serán invocados en tiempo de ejecución desde Azure Key Vault.
* **Privacidad por Diseño (Hashing de PII):** En la transición de Bronze a Silver, los datos directamente identificables (Documentos de Identidad, Teléfonos) serán sometidos a cifrado unidireccional (SHA-256). Solo mantendremos los *hashes* en las capas analíticas para mantener la integridad relacional.
* **Aislamiento Multi-Tenant (Row-Level Security - RLS):** En la capa semántica de la capa Gold, se configurarán filtros dinámicos basados en la función `USERPRINCIPALNAME()` de Entra ID. Esto asegura matemáticamente que el personal administrativo de una IPS nunca pueda consultar o decodificar métricas de una IPS ajena.

### D. Estimación de Capacidad, Costos y *Workload Isolation*
* **Capacidad (SKUs de Fabric):** El modelo de precios de Fabric se basa en *Capacity Units* (CU). Para el piloto actual y la absorción de las primeras 10 clínicas, un **SKU F8 (8 CUs)** (aprox. $1,000 USD/mes) proveerá el poder de cómputo necesario unificando todos los motores (Spark, SQL, Power BI). El modelo de pago por uso (Pay-As-You-Go) permite pausar la capacidad los fines de semana si no hay cargas operativas.
* **Aislamiento de Cargas (*Noisy Neighbor Problem*):** Un riesgo crítico es que el reentrenamiento de un modelo predictivo masivo sature los recursos, ralentizando los tableros de la Gerencia. Esto se mitiga en la arquitectura delegando el procesamiento pesado al motor de **Spark** sobre la capa Silver, el cual escala elásticamente de forma independiente, dejando el motor **SQL Endpoint** libre y dedicado exclusivamente a resolver las sentencias DAX/SQL de Power BI en la capa Gold.

### E. Integración Continua y Entornos (CI/CD)
La gestión del ciclo de vida del dato se manejará con prácticas modernas de DataOps:
* **Entornos Separados:** Se tendrán tres Workspaces físicos separados: Desarrollo (`WS-FB-{DOM}-DEV`), Pruebas (`QA`) y Producción (`PRD`).
* **Git Integration:** Fabric estará sincronizado de forma nativa con repositorios de **Azure DevOps**. Cada cambio en un Notebook o Pipeline de Data Factory será un *commit* en una rama funcional.
* **Deployment Pipelines:** La promoción de código desde DEV hasta PRD se hará mediante los *Fabric Deployment Pipelines*, aplicando reglas paramétricas para cambiar las cadenas de conexión (ej. para que el entorno de PRD solo lea de la base de datos de PRD). 

### F. Ecosistema de Inteligencia Artificial Avanzada
El consumo de la capa Gold no se limitará a Inteligencia de Negocios; habilitaremos capacidades avanzadas, de forma trazable y segura:

1. **Machine Learning Predictivo (Azure Machine Learning):**
   - **Entrenamiento (MLOps):** Los científicos de datos conectarán sus *Compute Instances* de Azure Machine Learning (AML) directamente a los datos de OneLake mediante accesos directos (*Shortcuts*), evitando copias de datos. Utilizaremos **MLFlow** para llevar un registro riguroso de cada experimento, validando hiperparámetros y detectando degradación del modelo (*Data Drift*).
   - **Inferencia:** El modelo final se empaquetará como un *Managed Online Endpoint*. Fabric Data Factory consumirá este Endpoint y almacenará las predicciones en una nueva tabla `Fact_Predicciones` en la capa Gold. Así, Power BI cruzará fácilmente "Ausentismo Real vs Predicho".

2. **IA Generativa y Agentes (Azure AI Foundry):**
   - En una segunda fase, integraremos **Azure AI Foundry** (anteriormente Azure AI Studio) para construir agentes conversacionales apoyados en la arquitectura RAG (*Retrieval-Augmented Generation*). 
   - A través de la librería **Semantic Link** de Microsoft, expondremos el modelo semántico de la capa Gold a Modelos de Lenguaje Grande (LLMs). Esto habilitará escenarios donde los gerentes puedan interactuar en lenguaje natural ("¿Genera un resumen de las causas principales de ausentismo en la IPS Sur la última semana?"), delegando a la IA la generación y ejecución segura de la consulta sobre datos certificados, respetando las políticas de RLS.

### G. Qué NO haríamos en Fabric y por qué
**Limitación arquitectónica:** Microsoft Fabric no es, bajo ninguna circunstancia, un sistema transaccional (OLTP).

No permitiríamos que los agentes del Contact Center o el aplicativo web de DonDoctor realicen inserciones (INSERT) o actualizaciones (UPDATE) registro por registro (CRUD) directamente sobre OneLake o el Data Warehouse de Fabric en tiempo real.
* **¿Por qué?** El formato Delta Parquet está diseñado para escritura en bloques y lectura analítica columnar (OLAP). Escribir a nivel de fila individual a alta concurrencia generará el problema de los archivos pequeños (*Small Files Problem*), fragmentando el lago de datos, destruyendo el rendimiento de las consultas y disparando los costos de transacciones. 
* La arquitectura correcta mantiene a SQL Server y MongoDB como los únicos dueños de la operación en tiempo real, mientras que Fabric se encarga asincrónicamente de asimilar y entregar inteligencia sobre esos datos a gran escala.
