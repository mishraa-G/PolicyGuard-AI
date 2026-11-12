"""Configuration management for PolicyGuard Enterprise Compliance RAG."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseModel):
    # LLM Settings (Supports: 'mock', 'gemini', 'openai')
    llm_provider: str = Field(default_factory=lambda: os.getenv("LLM_PROVIDER", "gemini" if os.getenv("GEMINI_API_KEY") else "mock"))
    
    # Gemini Configuration
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_API_KEY", "")))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))

    # OpenAI Configuration
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = Field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4o-mini"))
    embedding_model: str = Field(default_factory=lambda: os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"))
    embedding_dim: int = Field(default=384)

    # Qdrant Vector Store
    qdrant_location: str = Field(default_factory=lambda: os.getenv("QDRANT_LOCATION", str(BASE_DIR / "qdrant_storage")))
    qdrant_collection: str = Field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "enterprise_policies"))
    qdrant_url: str = Field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    qdrant_api_key: str = Field(default_factory=lambda: os.getenv("QDRANT_API_KEY", ""))

    # SQL Policy Database
    sqlite_db_path: str = Field(default_factory=lambda: os.getenv("SQLITE_DB_PATH", str(BASE_DIR / "data" / "policy_database.sqlite")))

    # Retrieval & Performance Parameters
    max_retrieval_chunks: int = Field(default=7)
    hybrid_rrf_k: int = Field(default=60)
    dense_weight: float = Field(default=0.6)
    sparse_weight: float = Field(default=0.4)
    latency_budget_ms: int = Field(default=800)
    guardrail_self_correct: bool = Field(default=True)

    # Paths
    raw_policies_dir: Path = BASE_DIR / "data" / "raw_policies"
    benchmarks_path: Path = BASE_DIR / "evaluation" / "benchmarks.json"

settings = Settings()
