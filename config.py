import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import BaseModel


class Paths(BaseModel):
    project_root: Path = Path(__file__).resolve().parent
    data_raw: Path = project_root / "data" / "raw"
    data_processed: Path = project_root / "data" / "processed"
    data_indices: Path = project_root / "data" / "indices"

    def setup(self):
        self.data_raw.mkdir(parents=True, exist_ok=True)
        self.data_processed.mkdir(parents=True, exist_ok=True)
        self.data_indices.mkdir(parents=True, exist_ok=True)


class AppConfig(BaseSettings):
    paths: Paths = Paths()
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 16
    vector_db_path: str = str(Paths().data_indices / "chroma")
    graph_db_url: str = "networkx" # Default prototype using networkx, could be bolt://localhost:7687
    openai_api_key: str = ""
    gemini_api_key: str = ""
    llm_provider: str = "google-genai" # Or openai

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


config = AppConfig()
config.paths.setup()

__all__ = ["config", "AppConfig", "Paths"]
