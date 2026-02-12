"""
Suite de pruebas del QUERY ENGINE
Valida: Evaluación semántica del AST sobre DataFrame real
"""

import pandas as pd

from core._3_input_controller import parse_pattern
from core._4_query_engine import run_query

# -------------------------------------------------------------------------
# CONFIGURACIÓN MOCK
# -------------------------------------------------------------------------
FAKE_CONFIG = {
    "processing": {
        "separator": ","
    },
    "components": {
        "Outlet_Temperature": [511],
        "MG-LV-MSB_Frequency": [475, 612]
    }
}

# -------------------------------------------------------------------------
# DATASET DE PRUEBA
# -------------------------------------------------------------------------
def build_df():
    """
    MultiIndex:
      level 0 -> obs_seq
      level 1 -> pred_seq
    """
    index = pd.MultiIndex.from_tuples(
        [
            ("475", "511"),
            ("475,511", "612"),
            ("475,123,511", "511"),
            ("123,511", "475"),
            ("475,612", "475"),
            ("612", "511"),
            ("475,612,511", "612"),
            ("511", "475"),
            ("612,511", "475"),
        ],
        names=["obs_seq", "pred_seq"]
    )

    return pd.DataFrame(
        {"value": range(len(index))},
        index=index
    )

# -------------------------------------------------------------------------
# HELPERS
# -------------------------------------------------------------------------
def run(src=None, dst=None):
    df = build_df()
    src_p = parse_pattern(src, "observation", FAKE_CONFIG) if src else None
    dst_p = parse_pattern(dst, "prediction", FAKE_CONFIG) if dst else None
    return run_query(df, src_p, dst_p, FAKE_CONFIG)

# -------------------------------------------------------------------------
# TESTS
# -------------------------------------------------------------------------
def test_atomic_value():
    res = run(src="475")
    assert all(res.index.get_level_values(0) == "475")

def test_exact_sequence():
    res = run(src="475,511")
    assert ("475,511", "612") in res.index

def test_anyone():
    res = run(src="475,?,511")
    assert ("475,123,511", "511") in res.index
    assert ("475,511", "612") not in res.index

def test_star_prefix():
    res = run(src="475,*")
    for v in res.index.get_level_values(0):
        assert v.startswith("475")

def test_star_suffix():
    res = run(src="*,511")
    for v in res.index.get_level_values(0):
        assert v.endswith("511")

def test_has():
    res = run(src="{511}")
    for v in res.index.get_level_values(0):
        assert "511" in v.split(",")

def test_and():
    res = run(src="475,* & {511}")
    assert ("475,123,511", "511") in res.index
    assert ("475,612", "475") not in res.index

def test_or():
    res = run(src="475 | 612")
    assert ("475", "511") in res.index
    assert ("612", "511") in res.index

def test_not():
    res = run(src="!{511}")
    for v in res.index.get_level_values(0):
        assert "511" not in v.split(",")

def test_alias_single():
    res = run(src="@Outlet_Temperature")
    assert ("511", "475") in res.index

def test_alias_multi():
    res = run(src="@MG-LV-MSB_Frequency")
    assert ("475", "511") in res.index
    assert ("612", "511") in res.index

def test_alias_or():
    res = run(src="@Outlet_Temperature | @MG-LV-MSB_Frequency")
    assert ("511", "475") in res.index
    assert ("475", "511") in res.index
    assert ("612", "511") in res.index

def test_src_dst_independent():
    res = run(src="475,*", dst="{511}")
    for obs, pred in res.index:
        assert obs.startswith("475")
        assert "511" in pred.split(",")

# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------
if __name__ == "__main__":
    print("🧪 Ejecutando tests del Query Engine...")
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ✅ {name}")
    print("🚀 Todos los tests del Query Engine OK")
