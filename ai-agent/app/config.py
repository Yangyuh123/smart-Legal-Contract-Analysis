"""Application configuration via Pydantic BaseSettings."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Server
    APP_NAME: str = "SmartLegal AI Agent"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ChromaDB
    CHROMA_PERSIST_DIR: str = "./data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "legal_knowledge"

    # Embeddings（基于字符bigram哈希的简易嵌入，零外部依赖）
    EMBEDDING_DIM: int = 384

    # File storage
    UPLOAD_DIR: str = "./data/uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB

    # RAG
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5
    USE_HYBRID_RETRIEVAL: bool = False  # 仅稠密向量检索（BM25混合暂不稳定）
    RAG_DENSE_WEIGHT: float = 0.7      # 稠密检索权重
    RAG_SPARSE_WEIGHT: float = 0.3     # BM25 稀疏检索权重

    # CORS
    ALLOWED_ORIGINS: str = "*"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",  # 忽略 .env 中 MySQL/Redis 等无关变量
    }


settings = Settings()
