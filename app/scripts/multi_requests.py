import time
import requests
import yaml
import json
from pathlib import Path
import sys

# -------------------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------------------
API_URL = "http://127.0.0.1:8050"  # Asegúrate de que este puerto coincide con tu uvicorn
QUERIES_FILE = Path(__file__).with_name("multi_requests_file.yml")

def load_queries():
    if not QUERIES_FILE.exists():
        print(f"❌ Error: No se encontró {QUERIES_FILE}")
        sys.exit(1)
    
    with QUERIES_FILE.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("queries", [])

def print_separator():
    print("-" * 60)

def main():
    print("🚀 Iniciando Simulación de Frontend (Test E2E Secuencial)")
    print(f"📡 Conectando a: {API_URL}")
    print_separator()

    # 1. Verificar que la API está viva (Health check básico)
    try:
        requests.get(f"{API_URL}/docs", timeout=2)
        print("✅ API detectada y respondiendo.")
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar a la API.")
        print("   -> Asegúrate de ejecutar 'uvicorn main:app --reload' en otra terminal.")
        sys.exit(1)

    queries = load_queries()
    print(f"📋 Consultas cargadas: {len(queries)}")
    print("\n📄 Contenido de queries.yml:")
    print(json.dumps(queries, indent=2, ensure_ascii=False))
    print_separator()

    # 2. Bucle Secuencial
    for i, q in enumerate(queries, start=1):
        src = q.get("src")
        dst = q.get("dst")
        
        print(f"\n▶️  EJECUTANDO CONSULTA #{i}")
        print(f"    SRC: {src}")
        print(f"    DST: {dst}")

        start_time = time.time()

        try:
            # --------------------------------------------------
            # PASO A: Solicitar cálculo de la query (POST)
            # --------------------------------------------------
            payload = {"src": src, "dst": dst}
            response = requests.post(f"{API_URL}/query", json=payload)
            
            if response.status_code != 200:
                print(f"    ❌ Fallo en la solicitud: {response.status_code}")
                print(f"    Mensaje: {response.text}")
                continue

            result = response.json()
            query_id = result["query_id"]
            rows_count = result["rows"]
            cached = result["cached"]
            
            elapsed = time.time() - start_time
            print(f"    ✅ Procesado en {elapsed:.2f}s | ID: {query_id}")
            print(f"    📊 Resultados: {rows_count} filas | Caché: {cached}")

            # --------------------------------------------------
            # PASO B: Si hay datos, obtener vista previa (GET Data)
            # --------------------------------------------------
            if rows_count > 0:
                # Simulamos la paginación del frontend pidiendo las primeras 3 filas
                data_url = f"{API_URL}/query/{query_id}/data?limit=3"
                data_resp = requests.get(data_url)
                
                if data_resp.status_code == 200:
                    data_json = data_resp.json()
                    rows = data_json["rows"]
                    
                    print(f"    👀 Vista previa (3 filas):")
                    for idx, row in enumerate(rows):
                        # Formateamos un poco para que no inunde la consola
                        # Mostramos solo el índice compuesto para verificar
                        obs_idx = list(row.keys())[0] # Asumiendo que el índice es la primera col visualmente
                        print(f"       {idx+1}. {row}")
                else:
                    print(f"    ⚠️ Error obteniendo datos: {data_resp.text}")

        except Exception as e:
            print(f"    ❌ Excepción durante la prueba: {e}")

        print_separator()
        # Pequeña pausa para ver los logs en tiempo real claramente
        time.sleep(0.5) 

    print("\n🏁 Todas las pruebas finalizadas.")

if __name__ == "__main__":
    main()