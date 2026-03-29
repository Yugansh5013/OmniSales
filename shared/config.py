"""Centralized configuration via pydantic-settings."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- LLM (Groq) ---
    groq_api_keys: str = ""  # comma-separated pool

    # --- Database (Neon Cloud PostgreSQL) ---
    database_url: str = "postgresql://neondb_owner:password@ep-example.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    neon_project_id: str = "small-lake-37805230"
    neon_branch_id: str = "br-frosty-cherry-a15xoyq0"

    # --- Redis ---
    redis_url: str = "redis://localhost:6379"

    # --- Kafka ---
    kafka_brokers: str = "localhost:9092"

    # --- Pinecone ---
    pinecone_api_key: str = ""
    pinecone_index: str = "omnisales-knowledge"

    # --- OpenAI Embeddings ---
    openai_api_key: str = ""

    # --- LangSmith ---
    langsmith_api_key: str = ""
    langchain_tracing_v2: bool = False
    langchain_project: str = "omnisales"

    # --- Multi-tenant ---
    org_id: str = "org_default"

    # --- MCP Server URLs ---
    mcp_approvals_url: str = "http://mcp-approvals:8004/mcp"
    mcp_knowledge_url: str = "http://mcp-knowledge:8003/mcp"
    mcp_crm_url: str = "http://mcp-crm:8001/mcp"

    # --- A2A ---
    spy_a2a_url: str = "http://spy-a2a:8080"

    # --- JWT ---
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 1440

    # ── Derived helpers ──

    @property
    def groq_key_pool(self) -> list[str]:
        """Return list of Groq API keys for rotation."""
        return [k.strip() for k in self.groq_api_keys.split(",") if k.strip()]

    @property
    def kafka_broker_list(self) -> list[str]:
        return [b.strip() for b in self.kafka_brokers.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance (cached)."""
    return Settings()
