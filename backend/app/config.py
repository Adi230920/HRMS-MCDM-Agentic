"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings schema."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    ROUTE_EXTRACTOR: str = (
        "groq:qwen/qwen3.8-27b,gemini:gemini-3.5-flash-lite,openrouter:openrouter/free"
    )
    ROUTE_TECHNICAL: str = (
        "gemini:gemini-3.5-flash-lite,groq:openai/gpt-oss-120b,"
        "openrouter:google/gemma-4-31b-it:free"
    )
    ROUTE_MANAGER: str = (
        "groq:openai/gpt-oss-120b,openrouter:openrouter/free,"
        "gemini:gemini-3.5-flash-lite"
    )
    ROUTE_HR: str = (
        "openrouter:openrouter/free,gemini:gemini-3.5-flash-lite,"
        "groq:qwen/qwen3.8-27b"
    )
    ROUTE_MODERATOR: str = (
        "gemini:gemini-3.5-flash-lite,groq:openai/gpt-oss-120b,openrouter:openrouter/free"
    )
    ROUTE_CHAIR: str = (
        "groq:openai/gpt-oss-120b,gemini:gemini-3.5-flash-lite,openrouter:openrouter/free"
    )

    MAX_CONCURRENCY: int = 1
    DATABASE_URL: str = "sqlite:///./talentcouncil.db"
    FRONTEND_ORIGIN: str = "http://localhost:3000"
    MOCK_LLM: bool = False


settings = Settings()

