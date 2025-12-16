# app/app1.py
from debug.debug import save_debug_info

from helpers.config_loader import load_config
from helpers.preprocessor import load_or_preprocess_dataset

config = load_config()
save_debug_info(config, filename="config_loaded", head="CONFIG FINAL")

df = load_or_preprocess_dataset(config)

save_debug_info(
    lambda: df.head(),
    filename="dataset_processed_head",
    head="DATASET PROCESADO (HEAD)"
)