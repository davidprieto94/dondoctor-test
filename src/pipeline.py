import os
import pandas as pd
import json
import hashlib

DATA_DIR = "dataset"
RAW_DIR = "data/raw"
CLEAN_DIR = "data/clean"
CONS_DIR = "data/consumption"

def ingest_raw():
    """Copia los datos originales a la capa raw (Simulación de ingesta cruda)"""
    print("Iniciando Ingesta Raw...")
    os.makedirs(RAW_DIR, exist_ok=True)
    
    norte = pd.read_csv(f"{DATA_DIR}/ips_norte_citas.csv")
    norte.to_parquet(f"{RAW_DIR}/ips_norte.parquet", index=False)
    
    sur = pd.read_csv(f"{DATA_DIR}/ips_sur_citas.csv")
    sur.to_parquet(f"{RAW_DIR}/ips_sur.parquet", index=False)
    
    occidente = pd.read_csv(f"{DATA_DIR}/ips_occidente_citas.csv", sep=";")
    occidente.to_parquet(f"{RAW_DIR}/ips_occidente.parquet", index=False)
    
    with open(f"{DATA_DIR}/whatsapp_eventos.jsonl", 'r') as f:
        wa_data = [json.loads(line) for line in f]
    pd.DataFrame(wa_data).to_parquet(f"{RAW_DIR}/whatsapp_eventos.parquet", index=False)

def process_clean():
    """Estandarización al Modelo Canónico, Tratamiento de PII y Reglas de Calidad"""
    print("Iniciando Capa Clean...")
    os.makedirs(CLEAN_DIR, exist_ok=True)
    
    norte = pd.read_parquet(f"{RAW_DIR}/ips_norte.parquet")
    norte['ips_origen'] = 'NORTE'
    
    sur = pd.read_parquet(f"{RAW_DIR}/ips_sur.parquet")
    sur['ips_origen'] = 'SUR'
    
    occidente = pd.read_parquet(f"{RAW_DIR}/ips_occidente.parquet")
    occidente['ips_origen'] = 'OCCIDENTE'
    
    # 1. Homologación de Esquema para Occidente
    occ_rename = {
        "id_cita": "cita_id",
        "id_paciente": "paciente_id",
        "edad_paciente": "edad",
        "genero": "sexo",
        "regimen_salud": "regimen",
        "fecha_hora_cita": "fecha_cita",
        "estado_cita": "estado",
        "id_cita_origen": "cita_origen_id"
    }
    occidente.rename(columns=occ_rename, inplace=True)
    
    # Homologación de estados
    mapa_estados = {
        'ATD': 'ATENDIDA',
        'CAN': 'CANCELADA',
        'NAS': 'NO_ASISTIO',
        'PEN': 'PENDIENTE',
        'CONF': 'CONFIRMADA',
        'REP': 'CANCELADA',
        'REAGENDADA': 'CANCELADA'
    }
    
    for df in [norte, sur, occidente]:
        if 'estado' in df.columns:
            df['estado'] = df['estado'].replace(mapa_estados)

    # 2. Tratamiento de PII en Sur (Hashing)
    if "documento_identidad" in sur.columns:
        sur["documento_identidad_hash"] = sur["documento_identidad"].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest() if pd.notnull(x) else x)
        sur.drop(columns=["documento_identidad"], inplace=True)
    if "telefono" in sur.columns:
        sur["telefono_hash"] = sur["telefono"].astype(str).apply(lambda x: hashlib.sha256(x.encode()).hexdigest() if pd.notnull(x) else x)
        sur.drop(columns=["telefono"], inplace=True)
                 
    # Concatenar
    citas_unificadas = pd.concat([norte, sur, occidente], ignore_index=True)
    
    # Cast fechas
    date_cols = ["fecha_creacion", "fecha_cita", "fecha_actualizacion"]
    for c in date_cols:
        citas_unificadas[c] = pd.to_datetime(citas_unificadas[c], errors='coerce')
        
    # 3. Reglas de Calidad (H3: Duplicidad, H4: Incoherencia)
    # Deduplicación
    citas_unificadas.sort_values(by="fecha_actualizacion", ascending=False, inplace=True)
    citas_unificadas.drop_duplicates(subset=["ips_origen", "cita_id"], keep="first", inplace=True)
                                       
    # Filtrar incoherencias temporales
    mask_incoherentes = citas_unificadas["fecha_creacion"] > citas_unificadas["fecha_cita"]
    incoherentes = citas_unificadas[mask_incoherentes]
    incoherentes.to_parquet(f"{CLEAN_DIR}/dlq_citas_incoherentes.parquet", index=False)
    
    citas_limpias = citas_unificadas[~mask_incoherentes]
    
    # Fail-fast (Automated DQ Tests)
    assert len(citas_limpias[citas_limpias["fecha_creacion"] > citas_limpias["fecha_cita"]]) == 0, "Prueba Fallida: Incoherencia temporal"
    assert citas_limpias.duplicated(subset=["ips_origen", "cita_id"]).sum() == 0, "Prueba Fallida: Duplicados"
    
    citas_limpias.to_parquet(f"{CLEAN_DIR}/citas_canonico.parquet", index=False)

def process_consumption():
    """Construcción del Modelo Dimensional (Star Schema)"""
    print("Iniciando Capa Consumption...")
    os.makedirs(CONS_DIR, exist_ok=True)
    citas = pd.read_parquet(f"{CLEAN_DIR}/citas_canonico.parquet")
    
    # Dimensión Paciente
    dim_cols = ["ips_origen", "paciente_id", "edad", "sexo", "regimen", "localidad"]
    dim_paciente = citas[[c for c in dim_cols if c in citas.columns]].drop_duplicates(subset=["ips_origen", "paciente_id"])
    dim_paciente.to_parquet(f"{CONS_DIR}/dim_paciente.parquet", index=False)
    
    # Dimensión IPS
    dim_ips = citas[["ips_origen", "sede"]].drop_duplicates()
    dim_ips.to_parquet(f"{CONS_DIR}/dim_ips.parquet", index=False)
    
    # Hechos Citas
    fact_cols = [
        "cita_id", "ips_origen", "paciente_id", "medico_id", "sede", 
        "canal_agendamiento", "fecha_creacion", "fecha_cita", "estado", 
        "recordatorio_enviado", "confirmada"
    ]
    fact_citas = citas[[c for c in fact_cols if c in citas.columns]].copy()
    
    # Métrica de Ausentismo
    def calc_ausentismo(estado):
        if estado == "NO_ASISTIO": return 1
        if estado == "ATENDIDA": return 0
        return None
        
    fact_citas["ind_ausentismo"] = fact_citas["estado"].apply(calc_ausentismo)
    
    fact_citas.to_parquet(f"{CONS_DIR}/fact_citas.parquet", index=False)
    print("Pipeline finalizado con éxito.")

if __name__ == "__main__":
    ingest_raw()
    process_clean()
    process_consumption()
