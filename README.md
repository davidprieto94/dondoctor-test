# DonDoctor Data Pipeline Piloto

Este repositorio contiene la prueba técnica para el rol de Líder e Ingeniero de Datos en DonDoctor.

## Requisitos y Configuración

El pipeline y modelo predictivo están desarrollados en Python utilizando **Pandas** y **Scikit-Learn**. Se eligió Pandas por sobre PySpark para la extracción piloto por su facilidad de ejecución local sin requerir configuraciones de JVM/Hadoop en la máquina destino, cumpliendo perfectamente con el volumen del piloto.

```bash
# Instalación de dependencias
pip install -r requirements.txt
```

*Nota:* Los datos fuente (`dataset/`) no están incluidos en el repositorio por seguridad. Deben ubicarse en la raíz del proyecto bajo la carpeta `dataset/` con los nombres:
- `ips_norte_citas.csv`
- `ips_sur_citas.csv`
- `ips_occidente_citas.csv`
- `whatsapp_eventos.jsonl`

## Ejecución del Pipeline (E4)

Para correr el pipeline de datos completo (Ingesta -> Clean -> Consumption):
```bash
python src/pipeline.py
```
El script generará una carpeta `data/` con las subcapas `raw`, `clean` y `consumption` en formato Parquet. El pipeline es **idempotente** (puede correrse N veces sin duplicar datos) e incluye aserciones automatizadas de calidad (DQ fail-fast).

### Limitaciones Conocidas
1. **In-Memory Processing:** Pandas carga todo en memoria. Para el piloto (decenas de miles de registros) es instantáneo, pero para producción (millones) esto debe migrar a PySpark en Azure Databricks o Microsoft Fabric (como se propone en la Arquitectura E3).
2. **Eventos de WhatsApp:** Se descubrió que los eventos proporcionados en el piloto no cruzan con ninguna cita de las 3 IPS (son eventos huérfanos). Se mantuvieron en raw, pero no se integraron al modelo dimensional final.

### ¿Qué haría con dos semanas adicionales?
1. Migrar la lógica exacta a **PySpark (Notebooks de Fabric)**.
2. Implementar **Great Expectations** o **Soda** para un framework de calidad de datos más robusto que las aserciones de Python, enviando alertas a Teams/Slack.
3. Usar **dbt (Data Build Tool)** para la capa de consumo, permitiendo linaje de datos y pruebas automáticas documentadas.
4. Orquestar el flujo con **Azure Data Factory** o **Airflow**.

## Documentación Adjunta
- `docs/E1_Diagnostico.md`: Análisis y calidad de los datos crudos.
- `docs/E2_Estrategia.md`: Definición de negocio y hoja de ruta.
- `docs/E3_Arquitectura.md`: Diseño propuesto en Azure/Fabric.
- `docs/E6_Resumen.md`: Resumen ejecutivo (One-pager).
- `USO-IA.md`: Declaración del uso de inteligencia artificial.
