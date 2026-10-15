import json
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///tradepilot.db"
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    api_docs_enabled: bool = True
    workflow_rate_limit_per_minute: int = 60
    ai_provider: str = "ollama"
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen3:8b"
    ollama_think: bool = False
    ollama_tag_timeout_seconds: float = 90.0
    semantic_search_enabled: bool = False
    embedding_provider: str = "huggingface"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_profiles_json: str = ""
    qdrant_url: str = "http://127.0.0.1:6333"
    qdrant_collection: str = "tradepilot_products"
    semantic_search_timeout_seconds: float = 10.0
    rag_explanations_enabled: bool = True
    reranker_enabled: bool = False
    reranker_model: str = "BAAI/bge-reranker-v2-m3"
    openai_compatible_api_key: str = ""
    openai_compatible_base_url: str = "https://api.openai.com/v1"
    openai_compatible_model: str = "gpt-4o-mini"
    openai_compatible_timeout_seconds: float = 45.0
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = 45.0
    kimi_api_key: str = ""
    kimi_base_url: str = "https://api.moonshot.cn/v1"
    kimi_model: str = "moonshot-v1-8k"
    kimi_timeout_seconds: float = 45.0
    product_keyword_weight: int = 20
    product_project_weight: int = 15
    product_quantity_weight: int = 15
    auth_enabled: bool = False
    auth_secret: str = ""
    auth_username: str = ""
    auth_password_hash: str = ""
    auth_role: str = "approver"
    auth_token_ttl_seconds: int = 3600
    auth_refresh_ttl_seconds: int = 604800

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def embedding_profile_options(self) -> list[dict[str, str]]:
        default = {"id": f"{self.embedding_provider}:{self.embedding_model}", "provider": self.embedding_provider, "model": self.embedding_model}
        try:
            configured = json.loads(self.embedding_profiles_json) if self.embedding_profiles_json.strip() else []
        except json.JSONDecodeError:
            configured = []
        profiles = [item for item in configured if isinstance(item, dict) and item.get("id") and item.get("provider") and item.get("model")]
        if not any(item["id"] == default["id"] for item in profiles):
            profiles.insert(0, default)
        return profiles


@lru_cache
def get_settings() -> Settings:
    return Settings()
