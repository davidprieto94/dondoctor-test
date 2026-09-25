# E6. Resumen Ejecutivo para la Gerencia General

**Objetivo:** Alinear a las áreas Operativa, Tecnológica y Comercial sobre la verdadera tasa de ausentismo, definir el plan de choque inmediato y pivotar la estrategia de monetización de datos para maximizar ingresos mitigando riesgos legales.

A continuación, presento el análisis consolidado y las recomendaciones de la Dirección de Datos:

### 1. ¿Cuál es el ausentismo real y por qué había discrepancias?
El ausentismo operativo real consolidado del piloto es del **14.5%**, y no la cifra inflada que percibían algunas áreas. 
Tras auditar el flujo de datos desde los sistemas de las IPS (SQL Server) hasta nuestro modelo, descubrimos que la discrepancia nacía de un error de clasificación: muchas citas que eran reagendadas a tiempo o canceladas proactivamente por el paciente se estaban contando como "ausentismos", castigando injustamente el indicador. 
Para resolver este debate definitivamente, hemos estandarizado los estados en un Modelo Canónico centralizado (Single Source of Truth) en nuestro Data Warehouse. A partir de hoy, Finanzas, Operaciones y Comercial consumirán exactamente el mismo dato gobernado.

### 2. ¿En qué IPS intervenir primero y con qué estrategia?
Debemos lanzar nuestro primer escuadrón de intervención en la **IPS Sur**. 
El análisis empírico revela que esta sede no solo presenta el peor desempeño operativo histórico, sino que además nuestro nuevo modelo de Machine Learning detectó un patrón crítico en su demografía: los pacientes del régimen subsidiado con un tiempo de espera (*Lead Time*) superior a 15 días tienen una probabilidad altísima de inasistencia.
**La acción:** En lugar de lanzar campañas masivas a ciegas, utilizaremos las predicciones del modelo para que el Call Center contacte exclusivamente a los pacientes de IPS Sur catalogados como "Alto Riesgo" **exactamente 48 horas antes** de su cita. Esto nos permitirá confirmar la asistencia o, en su defecto, liberar la silla a tiempo para reasignarla, demostrando el ROI del equipo de datos en las primeras dos semanas.

### 3. ¿Debemos lanzar los servicios propuestos por Comercial?
*   **Benchmark entre IPS (Reportes agregados): SÍ, LANZAR INMEDIATAMENTE.** Es un excelente servicio B2B para fidelizar a las IPS. Hemos diseñado la arquitectura en la nube (Microsoft Fabric) con Seguridad a Nivel de Fila (RLS) multi-tenant, lo que nos garantiza matemáticamente que podemos entregar métricas comparativas anonimizadas sin que una IPS pueda ver jamás los datos crudos de su competencia.
*   **Informe de riesgo nominal a EPS: NO LANZAR. DEBEMOS REDISEÑARLO.** Entregar listados directos perfilando a pacientes "riesgosos" a las aseguradoras (EPS) representa un riesgo ético y legal inasumible. Viola la ley de protección de datos (Habeas Data) al no contar con consentimiento para perfilamiento algorítmico, y expone a DonDoctor a ser cómplice de discriminación en el acceso a la salud.
    *   **El Pivot Estratégico:** En lugar de vender el "listado crudo", propondremos a las EPS venderles el **"Servicio de Gestión Proactiva"**. DonDoctor mantendrá el modelo bajo llave y utilizará a sus propios agentes para gestionar a esos pacientes de alto riesgo en nombre de la EPS. Cambiamos el modelo de negocio: ya no cobramos por vender datos, cobramos un *fee* por cada silla recuperada o paciente gestionado. Protegemos al paciente, blindamos a la compañía legalmente y capturamos más valor económico.