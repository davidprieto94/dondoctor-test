# E6. Resumen Ejecutivo

## Resumen Ejecutivo para la Gerencia General

**Objetivo:** Clarificar el ausentismo real y definir los próximos pasos estratégicos de monetización e intervención.

1. **¿Cuál es el ausentismo real?**
El ausentismo operativo real promedio es del **14.5%**. La discrepancia entre áreas se daba por la inclusión errónea de citas reagendadas a tiempo como ausentismos. Para gobernar esta cifra, hemos automatizado el cálculo en una capa centralizada (Single Source of Truth) en nuestro Data Warehouse. Nadie verá números distintos nuevamente.

2. **¿En qué IPS intervenir primero?**
Debemos intervenir inmediatamente la **IPS Sur**. El análisis de datos revela que presenta el peor desempeño operativo empírico y, además, nuestros modelos predictivos muestran una alta tasa de inasistencia predecible en su demografía. Intervenir Sur (con llamadas preventivas 48h antes) validará rápidamente el retorno de inversión (ROI) de la función de datos.

3. **¿Lanzar los servicios propuestos por Comercial?**
   - **Benchmark entre IPS:** **SÍ, LANZAR.** Es un excelente servicio B2B de retención de clientes. Validamos que nuestra arquitectura en Azure/Fabric puede aislar la información y generar estos reportes agregados y anonimizados sin riesgo de exponer datos de una IPS a otra.
   - **Informe de riesgo a EPS:** **NO LANZAR (REDISEÑAR).** Entregar listados nominales de pacientes "riesgosos" a las aseguradoras es un riesgo ético y legal severo (Habeas Data). En su lugar, propondremos a las EPS el servicio de **"Gestión Proactiva"**: DonDoctor se encarga de contactar y gestionar a esos pacientes de alto riesgo en nombre de la EPS, cobrando por silla recuperada. Así, generamos ingresos sin exponer al paciente a la discriminación.