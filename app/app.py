# app/app.py

import argparse
import sys
from datetime import datetime
from pathlib import Path

from numpy import save

from debug.debug import save_debug_info

from helpers._1_config_loader import load_config
from helpers._2_preprocessor import load_or_preprocess_dataset
from helpers._3_input_controller import parse_pattern
from helpers._4_query_engine import run_query
from helpers._5_output_writer import save_results

# 🆕 Visualización
from helpers._6_event_dictionary import build_event_dictionary
from helpers._7_text_renderer import render_windows_text

MODE_VIEW = True

# -------------------------------------------------------------------------
# CLI
# -------------------------------------------------------------------------

def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Filtrado de ventanas de eventos mediante patrones"
    )

    parser.add_argument(
        "--src",
        type=str,
        required=False,
        help="Patrón para observation_events (ej: 475,484,*)"
    )

    parser.add_argument(
        "--dst",
        type=str,
        required=False,
        help="Patrón para prediction_events (ej: 475,511)"
    )

    args = parser.parse_args()

    if not args.src and not args.dst:
        parser.error("Debes especificar al menos uno de: --src o --dst")

    return args


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------

def main():
    start_time = datetime.now()

    # 1️⃣ CLI
    args = parse_cli_args()

    # 2️⃣ Config
    try:
        config = load_config()
    except Exception as e:
        print(f"[ERROR] Configuración inválida: {e}")
        sys.exit(1)

    # 3️⃣ Dataset
    try:
        df = load_or_preprocess_dataset(config)
    except Exception as e:
        print(f"[ERROR] Error cargando dataset: {e}")
        sys.exit(1)

    # 4️⃣ Patrones
    src_pattern = None
    dst_pattern = None

    if args.src:
        try:
            src_pattern = parse_pattern(
                raw_pattern=args.src,
                column_type="observation",
                config=config
            )
        except Exception as e:
            print(f"[ERROR] Patrón --src inválido: {e}")
            sys.exit(1)

    if args.dst:
        try:
            dst_pattern = parse_pattern(
                raw_pattern=args.dst,
                column_type="prediction",
                config=config
            )
        except Exception as e:
            print(f"[ERROR] Patrón --dst inválido: {e}")
            sys.exit(1)

    # 5️⃣ Query
    try:
        result_df = run_query(
            df=df,
            src_pattern=src_pattern,
            dst_pattern=dst_pattern,
            config=config
        )
    except Exception as e:
        print(f"[ERROR] Error durante la consulta: {e}")
        sys.exit(1)

    # 6️⃣ Guardar parquet
    try:
        output_parquet = save_results(
            result_df,
            src_pattern=src_pattern,
            dst_pattern=dst_pattern,
            config=config
        )
    except Exception as e:
        print(f"[ERROR] No se pudo guardar el parquet: {e}")
        sys.exit(1)

    # ---------------------------------------------------------------------
    # 🆕 7️⃣ Visualización
    # ---------------------------------------------------------------------
    if MODE_VIEW is True:
        # event_dict = build_event_dictionary(
        #     Path(config["paths"]["dataset_dicctionary"])
        # )
        event_dict = build_event_dictionary(config)
# content_source: Any, filename: Optional[str] = "info_debug", directory: Optional[Path] = None, head: Optional[str] = None
        save_debug_info(
            content_source=event_dict,
            filename="event_dictionary_debug",
            head="Diccionario de eventos cargado"
        )

        render_windows_text(
            df=result_df,
            event_dict=event_dict,
            config=config,
            limit=20,
            offset=0,
        )

        # try:

            # components_cfg = load_components(
            #     Path("datasets/components.yml")
            # )

            # output_image = output_parquet.with_suffix(".png")

            # plot_windows(
            #     df=result_df,
            #     event_id_map=event_dict,
            #     components_cfg=components_cfg,
            #     output_path=output_image
            # )
        # except Exception as e:
        #     print(f"[WARN] No se pudo generar la visualización: {e}")
        #     output_image = None

        # 8️⃣ Feedback
        elapsed = (datetime.now() - start_time).total_seconds()

        print("✔ Consulta completada correctamente")
        print(f"  Coincidencias encontradas: {len(result_df)}")
        print(f"  Parquet generado: {output_parquet}")


        print(f"  Tiempo total: {elapsed:.3f}s")


# -------------------------------------------------------------------------
# Entry point
# -------------------------------------------------------------------------

if __name__ == "__main__":
    main()
