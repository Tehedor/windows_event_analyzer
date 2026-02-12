"""
Suite de Pruebas Exhaustiva para el DSL
Valida: Parsing, Generación de AST y Normalización (Canonical)
"""

from core._3_input_controller import parse_pattern
import traceback

# -------------------------------------------------------------------------
# Configuración de Mock para Alias Semánticos
# -------------------------------------------------------------------------
FAKE_CONFIG = {
    "components": {
        "Outlet_Temperature": [511],
        "MG-LV-MSB_Frequency": [475, 612]
    }
}

# -------------------------------------------------------------------------
# Diccionario de Pruebas: { Expresión Original: Nombre Canonical Esperado }
# -------------------------------------------------------------------------
TEST_SUITE = {
    # --- NIVEL 0: Secuenciales ---
    "475": "475",
    "475,511": "475-511",
    "475 , 511": "475-511",  # Test de limpieza de espacios

    # --- NIVEL 1: Atómicas (Wildcards) ---
    "475,?,511": "475-any-511",
    "475,*": "475-star",
    "*,511": "star-511",
    "475,*,?,612": "475-star-any-612",

    # --- NIVEL 2: Pertenencia ---
    "{511}": "has-511",
    "{12 | 13}": "has-12-or-13",
    "475,* & {511}": "475-star-and-has-511",

    # --- NIVEL 3: Lógicas Complejas ---
    "475 | 511": "475-or-511",
    "(484 | 511)": "484-or-511",  # Paréntesis no afectan nombre
    "475,484,* | 511,612,*": "475-484-star-or-511-612-star",
    "475,484,* & *,511": "475-484-star-and-star-511",
    
    # --- NIVEL 4: Negación ---
    "!13,14": "not-13-14",
    "!(475,484,*)": "not-475-484-star",
    "475,* & !{511}": "475-star-and-not-has-511",

    # --- NIVEL 5: Alias Semánticos ---
    "@Outlet_Temperature": "511",
    "@MG-LV-MSB_Frequency": "475-or-612",
    "@Outlet_Temperature | @MG-LV-MSB_Frequency": "475-or-511-or-612", # Ordenado alfabético/numérico
    
    # --- NIVEL 6: Casos de "Orden e Invarianza" ---
    # (El canonical debe ser el mismo aunque cambie el orden en el OR/AND)
    "511 | 475": "475-or-511", 
    "{13 | 12}": "has-12-or-13",
}

def run_comprehensive_tests():
    print("=" * 70)
    print(f"{' DSL EXHAUSTIVE VALIDATION ':-^70}")
    print("=" * 70)

    passed = 0
    failed = 0

    for expr, expected_canonical in TEST_SUITE.items():
        print(f"\nTESTING: {expr}")
        try:
            # 1. Ejecutar el parseo
            qp =  (expr, "observation", FAKE_CONFIG)
            
            # 2. Validar resultado contra la especificación
            actual_canonical = qp.canonical
            
            # Usamos assert para validar la lógica de normalización
            assert actual_canonical == expected_canonical, \
                f"Fallo en Normalización: Esperado '{expected_canonical}', obtenido '{actual_canonical}'"

            print(f"  ✅ STATUS: OK")
            print(f"  ✅ CANONICAL: {actual_canonical}")
            passed += 1

        except AssertionError as e:
            print(f"  ❌ STATUS: FAILED (Assertion)")
            print(f"     DETALLE: {e}")
            failed += 1
        except NotImplementedError:
            print(f"  ⚠️ STATUS: NOT IMPLEMENTED YET")
            failed += 1
        except Exception:
            print(f"  🔥 STATUS: CRITICAL ERROR")
            traceback.print_exc()
            failed += 1

    # --- RESUMEN FINAL ---
    print("\n" + "=" * 70)
    print(f" RESULTADOS FINALES ")
    print(f" TOTAL: {len(TEST_SUITE)} | PASSED: {passed} | FAILED: {failed}")
    print("=" * 70)

    if failed == 0:
        print("🚀 ¡Perfecto! El DSL cumple con toda la especificación de normalización.")
    else:
        print("🔧 Hay inconsistencias en el AST o el Parser. Revisa los errores arriba.")

if __name__ == "__main__":
    run_comprehensive_tests()