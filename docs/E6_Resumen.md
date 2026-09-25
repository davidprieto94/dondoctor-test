# E6. Resumen Ejecutivo y Guion del Video

## Resumen Ejecutivo para la Gerencia General

**Objetivo:** Clarificar el ausentismo real y definir los próximos pasos estratégicos de monetización e intervención.

1. **¿Cuál es el ausentismo real?**
El ausentismo operativo real promedio es del **14.5%**. La discrepancia entre áreas se daba por la inclusión errónea de citas reagendadas a tiempo como ausentismos. Para gobernar esta cifra, hemos automatizado el cálculo en una capa centralizada (Single Source of Truth) en nuestro Data Warehouse. Nadie verá números distintos nuevamente.

2. **¿En qué IPS intervenir primero?**
Debemos intervenir inmediatamente la **IPS Sur**. El análisis de datos revela que presenta el peor desempeño operativo empírico y, además, nuestros modelos predictivos muestran una alta tasa de inasistencia predecible en su demografía. Intervenir Sur (con llamadas preventivas 48h antes) validará rápidamente el retorno de inversión (ROI) de la función de datos.

3. **¿Lanzar los servicios propuestos por Comercial?**
   - **Benchmark entre IPS:** **SÍ, LANZAR.** Es un excelente servicio B2B de retención de clientes. Validamos que nuestra arquitectura en Azure/Fabric puede aislar la información y generar estos reportes agregados y anonimizados sin riesgo de exponer datos de una IPS a otra.
   - **Informe de riesgo a EPS:** **NO LANZAR (REDISEÑAR).** Entregar listados nominales de pacientes "riesgosos" a las aseguradoras es un riesgo ético y legal severo (Habeas Data). En su lugar, propondremos a las EPS el servicio de **"Gestión Proactiva"**: DonDoctor se encarga de contactar y gestionar a esos pacientes de alto riesgo en nombre de la EPS, cobrando por silla recuperada. Así, generamos ingresos sin exponer al paciente a la discriminación.

---

## Guion Recomendado para el Video (6-8 minutos)

*(Puntos clave para el candidato en el video, compartiendo pantalla sin diapositivas)*

*   **¿Qué fue lo que más te sorprendió de los datos y cómo lo descubriste?**
    *   *Sugerencia:* "Me sorprendió descubrir que los más de 38,000 eventos de WhatsApp estaban totalmente huérfanos; no cruzaban con ninguna de las tres IPS piloto. Lo descubrí corriendo mi script de validación de calidad de datos en Python, donde el cruce de llaves (`contexto.ref_cita` vs `cita_id`) dio cero coincidencias."
*   **¿Cuál fue la decisión más difícil y por qué la tomaste así?**
    *   *Sugerencia:* "Decidir no lanzar el informe de riesgo a las EPS. Fue difícil porque Comercial ya tenía interés y disposición de pago de las EPS. Pero mi rol como Líder de Datos es proteger a la empresa y al paciente. Vender listados perfilados podía generar demandas por uso indebido de datos y discriminación. Fue mejor pivotar el modelo de negocio hacia un servicio de gestión."
*   **¿Qué dejaste fuera y qué harías primero con 4 horas más?**
    *   *Sugerencia:* "Dejé fuera la implementación de *Great Expectations* para calidad de datos y el pipeline de CI/CD. Con 4 horas más, montaría el pipeline automatizado en Azure DevOps para que el código de PySpark/Pandas corra en Databricks o Fabric y valide la calidad antes de ingestar a la capa Gold."
*   **Elige un fragmento de tu código y explica por qué está escrito así.**
    *   *Sugerencia:* (Muestra `src/pipeline.py` en la parte del `hashlib` o `drop_duplicates`). "Escribí esta línea de enmascaramiento unidireccional (SHA-256) para la cédula y teléfono de la IPS Sur en la capa Bronze a Silver. Es vital porque si ingresamos PII directo al Data Warehouse sin encriptar, cualquier científico de datos podría ver datos sensibles. Es seguridad por diseño."
*   **Situación real de tu experiencia:**
    *   *(Aquí debes contar una anécdota tuya real donde dijiste que NO a una solicitud de datos).*
