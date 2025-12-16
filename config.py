"""Configuration management for the Email Assistant."""


import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(override=True)


class Config:
    """Application configuration loaded from environment variables."""

    # Email Configuration
    EMAIL_ID = os.getenv("EMAIL_ID", "")
    APP_PASSWORD = os.getenv("APP_PASSWORD", "")

    # Date Range for Email Fetching (required, no defaults)
    START_DATE = os.getenv("START_DATE", "")
    END_DATE = os.getenv("END_DATE", "")

    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "").lower()

    # Ollama Configuration
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_LLM_MODEL = os.getenv("OLLAMA_LLM_MODEL", "llama3.1:8b")
    OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "llama3.1:8b")

    # Gemini Configuration
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Vector Store Configuration
    CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_store")
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "emails")

    # LLM Configuration
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))

    # Query Configuration
    DEFAULT_RETRIEVAL_COUNT = int(os.getenv("DEFAULT_RETRIEVAL_COUNT", "50"))

    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        errors = []

        # Required email configuration
        if not cls.EMAIL_ID:
            errors.append("EMAIL_ID is required")
        if not cls.APP_PASSWORD:
            errors.append("APP_PASSWORD is required")

        # Required date range
        if not cls.START_DATE:
            errors.append("START_DATE is required (format: YYYY-MM-DD)")
        if not cls.END_DATE:
            errors.append("END_DATE is required (format: YYYY-MM-DD)")

        # Required LLM provider
        if not cls.LLM_PROVIDER:
            errors.append("LLM_PROVIDER is required (must be 'ollama' or 'gemini')")
        elif cls.LLM_PROVIDER not in ["ollama", "gemini"]:
            errors.append(
                f"LLM_PROVIDER must be 'ollama' or 'gemini', got '{cls.LLM_PROVIDER}'"
            )

        # Provider-specific validation
        if cls.LLM_PROVIDER == "ollama":
            if not cls.OLLAMA_BASE_URL:
                errors.append("OLLAMA_BASE_URL is required when LLM_PROVIDER=ollama")
            if not cls.OLLAMA_LLM_MODEL:
                errors.append("OLLAMA_LLM_MODEL is required when LLM_PROVIDER=ollama")
            if not cls.OLLAMA_EMBEDDING_MODEL:
                errors.append(
                    "OLLAMA_EMBEDDING_MODEL is required when LLM_PROVIDER=ollama"
                )
        elif cls.LLM_PROVIDER == "gemini":
            if not cls.GOOGLE_API_KEY:
                errors.append("GOOGLE_API_KEY is required when LLM_PROVIDER=gemini")

        if errors:
            raise ValueError(
                f"Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
            )

        return True


# Create a singleton config instance
config = Config()
