import time
import requests
import yaml
import json
from pathlib import Path
import sys
import os

# -------------------------------------------------------------------------
# CONFIGURACIÓN
# -------------------------------------------------------------------------
API_URL = "http://127.0.0.1:8050"  # Asegúrate de que este puerto coincida con tu uvicorn
QUERIES_FILE = Path(__file__).with_name("multi_requests_file.yml")
PREVIEW_LIMIT = int(os.getenv("PREVIEW_LIMIT", "3"))

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
    print("🚀 Iniciando Simulación de Frontend (Test E2E Asíncrono)")
    print(f"📡 Conectando a: {API_URL}")
    print(f"📊 Límite de vista previa: {PREVIEW_LIMIT} filas")
    print_separator()

    # 1. Verificar que la API está viva
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
            # PASO A: Iniciar la consulta (POST)
            # --------------------------------------------------
            payload = {"src": src, "dst": dst}
            response = requests.post(f"{API_URL}/query", json=payload)
            
            if response.status_code != 200:
                print(f"    ❌ Fallo en la solicitud inicial: {response.status_code}")
                print(f"    Mensaje: {response.text}")
                continue

            result = response.json()
            query_id = result["query_id"]
            
            print(f"    ⏳ Consulta encolada (ID: {query_id}). Esperando procesamiento...")

            # --------------------------------------------------
            # PASO B: Bucle de espera (Polling) hasta que acabe
            # --------------------------------------------------
            status = "running"
            rows_count = 0
            
            while status in ("running", "pending"):
                time.sleep(1) # Esperamos 1 segundo entre preguntas
                
                # Consultamos el estado de la query
                status_resp = requests.get(f"{API_URL}/query/{query_id}")
                if status_resp.status_code != 200:
                    print(f"    ❌ Error consultando el estado: {status_resp.status_code}")
                    break
                    
                status_data = status_resp.json()
                status = status_data.get("status")
                
                if status == "done":
                    rows_count = status_data.get("rows", 0)
                    print(f"    ✅ Estado: DONE")
                elif status == "error":
                    print(f"    ❌ Estado: ERROR -> {status_data.get('error')}")
                    break

            # Si salimos del bucle y no es DONE, saltamos a la siguiente
            if status != "done":
                continue

            elapsed = time.time() - start_time
            print(f"    ✅ Procesado total en {elapsed:.2f}s")
            print(f"    📊 Resultados reales: {rows_count} filas")

            # --------------------------------------------------
            # PASO C: Si hay datos, obtener vista previa (GET Data)
            # --------------------------------------------------
            if rows_count > 0:
                data_url = f"{API_URL}/query/{query_id}/data?limit={PREVIEW_LIMIT}"
                data_resp = requests.get(data_url)
                
                if data_resp.status_code == 200:
                    data_json = data_resp.json()
                    rows = data_json["rows"]
                    
                    print(f"    👀 Vista previa ({min(PREVIEW_LIMIT, len(rows))} filas):")
                    for idx, row in enumerate(rows):
                        print(f"       {idx+1}. {row}")
                else:
                    print(f"    ⚠️ Error obteniendo datos: {data_resp.text}")

        except Exception as e:
            print(f"    ❌ Excepción durante la prueba: {e}")

        print_separator()
        time.sleep(0.5) 

    print("\n🏁 Todas las pruebas finalizadas.")

if __name__ == "__main__":
    main()