from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Ollama Configuration
    ollama_host: str = "http://localhost:11434"
    embedding_model: str = "nomic-embed-text"
    chat_model: str = "llama3.2"

    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Storage Paths
    data_dir: Path = Path(__file__).parent.parent / "data"
    upload_dir: Path = Path(__file__).parent.parent / "data" / "uploads"
    chroma_dir: Path = Path(__file__).parent.parent / "data" / "chroma_db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

# Ensure directories exist
settings.upload_dir.mkdir(parents=True, exist_ok=True)
settings.chroma_dir.mkdir(parents=True, exist_ok=True)
