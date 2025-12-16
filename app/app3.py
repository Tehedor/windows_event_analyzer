#!/usr/bin/env python3

import argparse
import sys
from datetime import datetime

from numpy import save

from debug.debug import save_debug_info

from helpers.config_loader import load_config
from helpers.preprocessor import load_or_preprocess_dataset
from helpers.input_controller import parse_pattern
from helpers.query_engine import run_query
# from helpers.output_writer import save_results


def parse_cli_args():
    parser = argparse.ArgumentParser(
        description="Filtrado de ventanas por patrones de eventos"
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
        parser.error("Debes especificar al menos --src o --dst")

    return args


def main():
    start_time = datetime.now()

    # 1️⃣ CLI
    args = parse_cli_args()

    # 2️⃣ Configuración
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

    # 4️⃣ Procesar patrones
    src_pattern = None
    dst_pattern = None

    if args.src:
        src_pattern = parse_pattern(
            raw_pattern=args.src,
            column_type="observation",
            config=config
        )

    if args.dst:
        dst_pattern = parse_pattern(
            raw_pattern=args.dst,
            column_type="prediction",
            config=config
        )

    # 5️⃣ Ejecutar consulta
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

    # 6️⃣ Guardar resultados
    try:
        # output_path = save_results(
        #     result_df,
        #     src_pattern=src_pattern,
        #     dst_pattern=dst_pattern,
        #     config=config
        # )
        save_debug_info(
            result_df,
            filename="query_result",
            head="RESULTADO DE LA CONSULTA"
        )

    except Exception as e:
        print(f"[ERROR] No se pudo guardar la salida: {e}")
        sys.exit(1)

    # 7️⃣ Feedback
    elapsed = (datetime.now() - start_time).total_seconds()

    print("✔ Consulta completada")
    print(f"  Coincidencias: {len(result_df)}")
    # print(f"  Archivo: {output_path}")
    print(f"  Tiempo: {elapsed:.2f}s")


if __name__ == "__main__":
    main()
