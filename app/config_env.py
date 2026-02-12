# config_env.py — configuración centralizada con Pydantic Settings
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json
from typing import Optional

class Settings(BaseSettings):
    # --- SERVER CONFIG ---
    SERVER_PORT: int = 8050

    DATASET_RAW_PATH: str = "datasets/raw/03_windows_dataset_tobs60_tpred30_tlead10.parquet"
    DATASET_PROCESSED_PATH: str = "datasets/processed/03_windows_dataset_tobs60_tpred30_tlead10_indexed.parquet"
    OUTPUT_DIR: str = "output/queries"
    OUTPUT_DIR_CSV: str = "output/queries_csv"
    DATASET_DICTIONARY_PATH: str = "datasets/raw/02_EventDictionary_notebook.json"

    OBS_EVENTS_COLUMN: str = "observation_events"
    PRED_EVENTS_COLUMN: str = "prediction_events"
    PERCENTILES: Optional[list] = ["Q05", "Q10", "Q20", "Q50", "Q90", "Q95"]

    # Configuración de carga
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore" # Ignora variables en el .env que no estén definidas aquí
    )

# Instancia global
settings_env = Settings()