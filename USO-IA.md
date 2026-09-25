# Declaración de Uso de IA (USO-IA.md)

De acuerdo con la sección 2.3 de las reglas de la prueba técnica, declaro el uso de herramientas de Inteligencia Artificial como asistencia durante la ejecución del ejercicio.

### Herramientas utilizadas y en qué partes del ejercicio:
1. **Modelos LLM (Gemini / ChatGPT):** 
   - Utilizados principalmente como un *pair programmer* para estructurar rápidamente el código boilerplate de Pandas/PySpark y Scikit-Learn en los entregables E4 (Pipeline) y E5 (Modelo).
   - Se usaron para revisar redacción técnica y asegurar coherencia en el documento de arquitectura (E3).
   - Se usaron como apoyo para idear la estructura del diagrama en sintaxis Mermaid.

### Ejemplo de algo que la IA propuso y que corregí o descarté:
* **El uso del campo estado:** Originalmente, en la etapa de estandarización, la IA sugirió mapear el estado `REAGENDADA` y `REP` de Occidente a un nuevo estado `REPROGRAMADA` en la capa limpia. **Lo descarté y modifiqué el código** porque, operativamente, una reagendación previa al día de la cita cuenta como una cita **CANCELADA** (a tiempo) y libera el hueco. Si la marcaba como `REPROGRAMADA`, podría inflar los denominadores de los reportes de ausentismo o crear ambigüedad en el Data Warehouse. Corregí el mapeo para que se alineara estrictamente a la ontología del negocio.

### Ejemplo de algo que resolví sin IA y por qué consideré que no aportaba:
* **El diseño del tratamiento ético/legal (E2 y E6):** La recomendación de *no vender listados de pacientes a las EPS sino ofrecer un servicio de gestión proactiva* fue generada completamente basándome en experiencia previa de negocio y leyes de protección de datos (Habeas Data en Colombia). La IA tiende a sugerir enfoques muy tecnicistas (como aplicar privacidad diferencial o federated learning), pero en la realidad corporativa, la solución más robusta suele ser cambiar el modelo de negocio o el contrato de servicio en lugar de complicar la ingeniería. Consideré que el enfoque humano en la negociación comercial aportaba más valor práctico.
