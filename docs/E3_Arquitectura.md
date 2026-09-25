# E3. Arquitectura Objetivo en Azure y Microsoft Fabric

## 1. Diagrama de Arquitectura

```mermaid
graph TD
    %% Fuentes de Datos
    subgraph Fuentes Transaccionales
        SQL_Norte[(SQL Server<br>IPS Norte)]
        SQL_Sur[(SQL Server<br>IPS Sur)]
        SQL_Occ[(SQL Server<br>IPS Occidente)]
        Mongo[(MongoDB<br>Eventos WhatsApp)]
    end

    %% Ingesta
    subgraph Ingesta - Azure Data Factory / Fabric Pipelines
        ADF[Data Factory Pipelines<br>Extracción Incremental]
    end

    %% Capas OneLake (Medallion Architecture)
    subgraph Microsoft Fabric OneLake
        subgraph Bronze Layer [Capa Bronze / Cruda]
            Delta_B[(Archivos Delta<br>Datos Originales)]
        end
        
        subgraph Silver Layer [Capa Silver / Limpia]
            Delta_S[(Modelo Canónico<br>Calidad y Homologación)]
            Hash[Enmascaramiento<br>de PII]
        end
        
        subgraph Gold Layer [Capa Gold / Consumo]
            Fact_Citas[(Hechos Citas)]
            Dim_Pacientes[(Dim Pacientes)]
            Dim_IPS[(Dim IPS)]
        end
    end

    %% Consumo y Exposición
    subgraph Capa Semántica y Consumo
        PowerBI[Power BI<br>Tableros Gerenciales]
        RLS[Row/Column Level Security]
        ML[Modelos Predictivos<br>Azure ML / Fabric Data Science]
        Agents[Agentes IA<br>Semantic Link]
    end

    %% Flujos
    SQL_Norte --> ADF
    SQL_Sur --> ADF
    SQL_Occ --> ADF
    Mongo --> ADF
    ADF -->|Append Only| Delta_B
    Delta_B -->|Transformación Spark| Delta_S
    Delta_S -->|Star Schema| Gold Layer
    Gold Layer --> RLS
    RLS --> PowerBI
    Gold Layer --> ML
    Gold Layer --> Agents
```

## 2. Documento de Decisiones Arquitectónicas

### A. Ingesta sin afectar la operación
* **SQL Server:** Se implementará un patrón de **Ingesta Incremental (Change Data Capture - CDC)** si está habilitado en las bases de datos de origen, o en su defecto, ingesta por marca de agua (Watermarking) basada en la columna `fecha_actualizacion`. La extracción se programará en ventanas de bajo tráfico operativo (madrugada).
* **MongoDB:** Se utilizará un conector nativo en Fabric/ADF con lectura paginada sobre índices (ej. filtrando por timestamp de evento) o leyendo directamente de un nodo secundario (réplica) del cluster de MongoDB para asegurar que no haya bloqueo de lectura/escritura en la base de datos principal.

### B. Organización por capas y Modelo Canónico multi-cliente
Implementaremos una **Arquitectura Medallón sobre OneLake (Formato Delta Parquet)**:
* **Bronze (Cruda):** Tablas anexas por cliente que respetan el esquema original al 100%. Los datos entran como "append-only".
* **Silver (Limpia - Modelo Canónico):** Un pipeline de Spark/SQL lee de Bronze y aplica homologación. Aunque los clientes tengan diferentes columnas (ej. `id_cita` vs `cita_id`), el código de transformación mapea todo a una tabla central `citas_silver` que tiene la estructura del diccionario canónico. Aquí se resuelven tipos de datos y se filtran duplicados técnicos.
* **Gold (Consumo):** Modelado Dimensional (Estrella) agrupando hechos (Citas) y dimensiones (IPS, Pacientes, Tiempo).

### C. Visibilidad y Seguridad de PII
1. **Column-Level Security (CLS) y Enmascaramiento:** En el paso de Bronze a Silver, columnas como `documento_identidad` y `telefono` pasan por una función de Hashing unidireccional (SHA-256) con un "salting" seguro resguardado en Azure Key Vault. Nadie, excepto procesos estrictamente autorizados, ve el PII crudo.
2. **Row-Level Security (RLS) Multi-tenant:** En la capa Semántica (Direct Lake / Gold), se implementará RLS usando la dimensión de IPS (ej. `WHERE ips_id = user_principal_ips`). Así, cuando un usuario de la IPS Norte ingrese a Power BI, el motor filtra a bajo nivel y solo visualizará datos de la IPS Norte.

### D. Estimación de Capacidad, Costos y Manejo de Cargas Pesadas
* **Supuestos:** Volúmenes actuales son bajos en el piloto (millares), pero escalando a decenas de IPS, estimamos 10 GB diarios de nueva data cruda y consultas recurrentes.
* **Costo / Capacidad:** En Fabric, esto se gestiona mediante "Capacidades" (SKUs F). Para arrancar, un SKU F2 o F8 (pago por uso) será suficiente, oscilando entre ~$250 a $1,000 USD/mes.
* **Aislamiento de Cargas (Workload Isolation):** Para evitar que el entrenamiento de un modelo de IA pesado afecte los dashboards de gerencia, en Fabric aprovecharemos la separación de Cómputo y Almacenamiento. OneLake es la base común, pero el SQL Endpoint (usado por Power BI) y los Spark Pools (usados para transformación y ML) utilizan nodos de cómputo independientes bajo la misma capacidad, pero priorizables mediante Workload Management (WLM) para dar prioridad de recursos a las consultas interactivas de Power BI.

### E. Ambientes de Desarrollo, Pruebas y Producción
Utilizaremos **Workspaces separados** en Fabric (WS_Dev, WS_Test, WS_Prod), controlados por **Git Integration** (Azure DevOps o GitHub) y Fabric Deployment Pipelines. 
* Los desarrolladores usarán repositorios de código para las notebooks de Spark y definiciones de SQL. 
* Los datos crudos en WS_Dev serán un muestreo anonimizado, no la base completa, para evitar fugas de datos en desarrollo.

### F. Consumo de Modelos de IA de forma Trazable
Los modelos y agentes accederán a los datos mediante la capa Gold utilizando **Semantic Link** de Microsoft Fabric. Esto permite que los notebooks de Python lean directamente las métricas gobernadas (el ausentismo oficial) sin tener que recalcularlas en el código. Las predicciones del modelo se guardarán como una tabla "Fact_Predicciones" de vuelta en OneLake, permitiendo que Power BI cruce lo que el modelo predijo versus lo que realmente sucedió, habilitando un bucle de monitoreo de ML (MLOps) y trazabilidad completa.

### G. Qué NO haríamos en Fabric y por qué
**No usaríamos Fabric como base de datos transaccional (OLTP) ni como backend para la aplicación de agendamiento en tiempo real.**
* **Por qué:** Fabric (y OneLake) está diseñado nativamente para cargas de trabajo analíticas (OLAP), procesando grandes volúmenes de datos orientados a columnas (Parquet/Delta). Intentar que DonDoctor conecte su aplicación web o WhatsApp bot directamente a Fabric para insertar una cita una a una con latencia de milisegundos y consistencia ACID inmediata sería un desastre de rendimiento y costo. Para la operación se debe mantener SQL Server / MongoDB, y Fabric se reserva para el análisis de esos datos.
