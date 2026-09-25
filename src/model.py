import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import warnings

warnings.filterwarnings('ignore')

CONS_DIR = "data/consumption"

def run_model():
    print("="*50)
    print(" E5. MODELO PREDICTIVO DE AUSENTISMO")
    print("="*50)
    
    print("\n1. DECISIÓN DE NEGOCIO Y MOMENTO DE PREDICCIÓN")
    print("- Decisión habilitada: Intervenir proactivamente (llamada/WhatsApp humano) a los pacientes con alto riesgo de inasistencia para confirmar, cancelar a tiempo, o agendar transporte.")
    print("- Momento exacto: 48 horas antes de la cita. Esto da tiempo suficiente a Operaciones para gestionar la lista y, si hay cancelaciones, ofrecer la cita a pacientes en lista de espera.")
    
    # Cargar datos
    try:
        fact_citas = pd.read_parquet(f"{CONS_DIR}/fact_citas.parquet")
        dim_paciente = pd.read_parquet(f"{CONS_DIR}/dim_paciente.parquet")
    except FileNotFoundError:
        print("Error: Ejecuta pipeline.py primero para generar la capa de consumo.")
        return
        
    # Cruce
    data = pd.merge(fact_citas, dim_paciente, on=["ips_origen", "paciente_id"], how="inner")
    
    print("\n2. VARIABLE OBJETIVO Y SELECCIÓN DE VARIABLES")
    print("- Variable Objetivo (Target): 'ind_ausentismo' (1 si NO_ASISTIO, 0 si ATENDIDA). Se excluyen cancelaciones a tiempo porque operativamente la silla no quedó vacía sin previo aviso.")
    
    # Preparar dataset
    data = data.dropna(subset=["ind_ausentismo"])
    
    # Feature Engineering Simple
    data["fecha_creacion"] = pd.to_datetime(data["fecha_creacion"])
    data["fecha_cita"] = pd.to_datetime(data["fecha_cita"])
    data["lead_time_dias"] = (data["fecha_cita"] - data["fecha_creacion"]).dt.days
    
    # Variables a usar
    features = ["edad", "sexo", "regimen", "canal_agendamiento", "ips_origen", "lead_time_dias"]
    X = data[features].copy()
    y = data["ind_ausentismo"].astype(int)
    
    print("- Features seleccionadas:")
    print("  * 'lead_time_dias': Citas agendadas con mucha anticipación suelen tener mayor ausentismo.")
    print("  * 'canal_agendamiento': Usuarios de canales digitales pueden comportarse distinto a los de call center.")
    print("  * 'edad' y 'regimen': Factores socioeconómicos y demográficos que impactan la movilidad.")
    print("  * 'ips_origen': La ubicación geográfica influye.")
    print("- Variables descartadas:")
    print("  * 'medico_id' / 'especialidad': Podrían sobreajustar el modelo inicial por alta cardinalidad. Se pueden incluir en V2.")
    
    print("\n3. ESTRATEGIA DE VALIDACIÓN")
    print("- Estrategia: Train-Test Split (80/20) estratificado. Idealmente, en un entorno real con más historia, usaríamos validación Out-of-Time (entrenar con meses pasados, probar con el último mes) para simular el paso del tiempo.")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Preprocesamiento
    numeric_features = ["edad", "lead_time_dias"]
    categorical_features = ["sexo", "regimen", "canal_agendamiento", "ips_origen"]
    
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())])
        
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))])
        
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
        
    print("\n4. ENTRENAMIENTO Y MÉTRICA PRINCIPAL")
    print("- Métrica Principal: Recall (Sensibilidad) de la clase 1 (Ausentismo).")
    print("- ¿Por qué?: El costo de un Falso Positivo (llamar a un paciente que sí iba a ir) es muy bajo: solo cuesta el tiempo del agente del call center y se refuerza la cita. El costo de un Falso Negativo (no llamar a quien va a faltar) es alto: una hora de especialista perdida. Por tanto, queremos atrapar la mayor cantidad posible de ausentes (alto Recall), incluso si baja un poco la precisión.")
    
    # Modelo Base: Regresión Logística
    clf_base = Pipeline(steps=[('preprocessor', preprocessor),
                               ('classifier', LogisticRegression(class_weight='balanced', random_state=42))])
    clf_base.fit(X_train, y_train)
    y_pred_base = clf_base.predict(X_test)
    
    print("\n--- Resultados Modelo Base (Regresión Logística) ---")
    print(classification_report(y_test, y_pred_base))
    
    # Modelo Elaborado: Random Forest
    clf_rf = Pipeline(steps=[('preprocessor', preprocessor),
                             ('classifier', RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, max_depth=5))])
    clf_rf.fit(X_train, y_train)
    y_pred_rf = clf_rf.predict(X_test)
    
    print("\n--- Resultados Modelo Elaborado (Random Forest) ---")
    print(classification_report(y_test, y_pred_rf))
    
    print("\n5. ANÁLISIS DE COMPORTAMIENTO POR GRUPOS Y USO RESPONSABLE (ÉTICA)")
    # Análisis simple de fairness
    test_results = X_test.copy()
    test_results['y_true'] = y_test
    test_results['y_pred'] = y_pred_rf
    
    print("Tasa de predicción de ausentismo por Régimen de Salud:")
    tasas = test_results.groupby('regimen').apply(lambda x: x['y_pred'].mean() * 100).round(1)
    print(tasas)
    
    print("\n- Implicación Ética: Si el modelo predice sistemáticamente que los pacientes del régimen subsidiado (menores ingresos) van a faltar más, y basamos decisiones punitivas en esto, estamos penalizando la pobreza. El modelo refleja desigualdades estructurales (falta de transporte, permisos laborales).")
    
    print("\n6. RECOMENDACIÓN FINAL")
    print("- PARA QUÉ USARLO: Para generar una lista priorizada de pacientes a quienes ofrecerles **ayuda** (facilidades de reagendamiento, subsidio de transporte, recordatorios humanos).")
    print("- PARA QUÉ NO USARLO: Nunca usarlo para cancelar citas unilateralmente (overbooking automático severo) ni para reportar 'riesgo' a las aseguradoras para que les nieguen servicios futuros. Eso vulneraría derechos del paciente.")

if __name__ == "__main__":
    run_model()
