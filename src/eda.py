import pandas as pd
import json

def analyze_data():
    # Cargar datos
    print("--- Perfilamiento General ---")
    norte = pd.read_csv('dataset/ips_norte_citas.csv')
    print(f"IPS Norte: {len(norte)} registros. Columnas: {list(norte.columns)}")
    
    sur = pd.read_csv('dataset/ips_sur_citas.csv')
    print(f"IPS Sur: {len(sur)} registros. Columnas: {list(sur.columns)}")
    
    occidente = pd.read_csv('dataset/ips_occidente_citas.csv', sep=';')
    print(f"IPS Occidente: {len(occidente)} registros. Columnas: {list(occidente.columns)}")
    
    with open('dataset/whatsapp_eventos.jsonl', 'r') as f:
        eventos = [json.loads(line) for line in f]
    print(f"WhatsApp: {len(eventos)} eventos.")
    
    print("\n--- Hallazgos ---")
    # H1: PII en Sur
    print(f"H1 - PII en Sur: Columnas sensibles presentes: {[c for c in ['documento_identidad', 'telefono'] if c in sur.columns]}")
    
    # H2: Inconsistencia Esquemas
    print(f"H2 - Estados Occidente: {occidente['estado_cita'].unique().tolist() if 'estado_cita' in occidente.columns else 'N/A'}")
    if 'estado' in norte.columns:
        print(f"H2 - Estado REAGENDADA en Norte: {len(norte[norte['estado'] == 'REAGENDADA'])}")
        
    # H3: Duplicidad
    print(f"H3 - Duplicados Norte (cita_id): {norte.duplicated(subset=['cita_id']).sum() if 'cita_id' in norte.columns else 'N/A'}")
    print(f"H3 - Duplicados Sur (cita_id): {sur.duplicated(subset=['cita_id']).sum() if 'cita_id' in sur.columns else 'N/A'}")
    
    # H4: Incoherencia temporal
    if 'fecha_creacion' in norte.columns and 'fecha_cita' in norte.columns:
        norte['fecha_creacion'] = pd.to_datetime(norte['fecha_creacion'])
        norte['fecha_cita'] = pd.to_datetime(norte['fecha_cita'])
        print(f"H4 - Incoherencia Norte (creacion > cita): {len(norte[norte['fecha_creacion'] > norte['fecha_cita']])}")
        
    if 'fecha_creacion' in sur.columns and 'fecha_cita' in sur.columns:
        sur['fecha_creacion'] = pd.to_datetime(sur['fecha_creacion'])
        sur['fecha_cita'] = pd.to_datetime(sur['fecha_cita'])
        print(f"H4 - Incoherencia Sur (creacion > cita): {len(sur[sur['fecha_creacion'] > sur['fecha_cita']])}")
        
    # H5: Eventos huérfanos
    citas_ids = set(norte['cita_id']).union(set(sur['cita_id'])).union(set(occidente.get('id_cita', [])))
    eventos_citas_ids = set([e.get('contexto', {}).get('ref_cita') for e in eventos])
    huerfanos = len([e for e in eventos if e.get('contexto', {}).get('ref_cita') not in citas_ids])
    print(f"H5 - Eventos huérfanos WhatsApp: {huerfanos}")

if __name__ == '__main__':
    analyze_data()
