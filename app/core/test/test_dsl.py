"""
Test rápido del DSL (input_controller)
Ejecución:
    python -m core.test.test_dsl
"""

from core._3_input_controller import parse_pattern


# -------------------------------------------------------------------------
# Config mínima fake (solo lo necesario para pasar asserts)
# -------------------------------------------------------------------------
FAKE_CONFIG = {
    "paths": {}
}


# -------------------------------------------------------------------------
# Casos de prueba
# -------------------------------------------------------------------------
TEST_CASES = [
    # simples
    "475",
    "475,511",
    "475,*",
    "475,?,511",

    # espacios y formatos
    " 475 , 511 ",
    "475 511",
    "475.511.*",

    # futuros (ahora fallarán, y está bien)
    "(475 | 511)",
    "475,* & {511}",
    "!475,511",
]


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------
def run_tests():
    print("=" * 60)
    print(" DSL QUICK TEST ")
    print("=" * 60)

    for expr in TEST_CASES:
        print("\n" + "-" * 40)
        print(f"INPUT: {expr!r}")

        try:
            qp = parse_pattern(expr, "observation", FAKE_CONFIG)

            print("STATUS: OK")
            print("CANONICAL:", qp.canonical)
            print("AST:", qp.ast)

        except AssertionError as e:
            print("STATUS: ASSERTION FAILED")
            print("ERROR :", e)

        except NotImplementedError as e:
            print("STATUS: NOT IMPLEMENTED")
            print("ERROR :", e)

        except Exception as e:
            print("STATUS: ERROR")
            print("TYPE  :", type(e).__name__)
            print("ERROR :", e)


# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------
if __name__ == "__main__":
    run_tests()
