# app/app1.py
from debug.debug import save_debug_info

from helpers.config_loader import load_config
from helpers.preprocessor import load_or_preprocess_dataset
from helpers.input_controller import parse_pattern

config = load_config()
save_debug_info(config, filename="config_loaded", head="CONFIG FINAL")

# df = load_or_preprocess_dataset(config)

# save_debug_info(
#     lambda: df.head(),
#     filename="dataset_processed_head",
#     head="DATASET PROCESADO (HEAD)"
# )


pattern = parse_pattern("12.3.*", "observation", config)

print(pattern)
