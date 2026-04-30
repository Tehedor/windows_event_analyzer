# config_env.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # --- SERVER CONFIG ---
    SERVER_PORT: int = 8050

    # --- DYNAMIC EXECUTION CONFIG ---
    # Versión específica a cargar (Variable de entorno clave)
    WINDOW_VERSION: str = "v001"
    # Ruta base donde están las ejecuciones (apunta a la carpeta 03)
    DATASET_RAW_PATH: str = "executions/f03_windows"
    PARQUET_NAME: str = "03_windows.parquet"
    METADATA_NAME: str = "03_preparewindowsds_metadata.json"

    DICTIONARY_NAME: str = "03_events_catalog.json"
    DATASET_RAM_TIMEOUT: int = 10

    # --- PROCESSED CONFIG ---
    # Ruta base para guardar los procesados. 
    # El nombre del archivo final se calculará automáticamente usando la versión (ej: ..._v001_indexed.parquet)
    DATASET_PROCESSED_PATH: str = "datasets/processed"

    # --- OUTPUTS ---
    # OUTPUT_DIR: str = "output/queries"
    # OUTPUT_DIR_CSV: str = "output/queries_csv"
    OUTPUT_DIR: str = "/app/output"

    # --- COLUMN NAMES (Overrides) ---
    # OBS_EVENTS_COLUMN: str = "observation_events"
    # PRED_EVENTS_COLUMN: str = "prediction_events"
    OBS_EVENTS_COLUMN: str = "OW_events"
    PRED_EVENTS_COLUMN: str = "PW_events"

    COMPONENTS_CTRL: str = "./components.yml"
    # COMPONENTS_CTRL: str = "datasets/components.yml"

    # Percentiles: Se intentarán cargar del metadata del padre, 
    # pero se pueden forzar aquí si es necesario.
    # PERCENTILES: Optional[list] = None 

    # Configuración de carga
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instancia global
settings_env = Settings()