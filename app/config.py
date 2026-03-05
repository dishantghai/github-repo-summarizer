import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # API Configuration
    NEBIUS_API_KEY: str = os.getenv("NEBIUS_API_KEY", "")
    NEBIUS_BASE_URL: str = "https://api.studio.nebius.com/v1"
    NEBIUS_MODEL: str = os.getenv("NEBIUS_MODEL", "meta-llama/Llama-3.3-70B-Instruct")

    # Alternative LLM providers (fallback)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # GitHub Configuration
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_RAW_BASE: str = "https://raw.githubusercontent.com"
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")

    # Context Management
    MAX_CONTEXT_TOKENS: int = 12000
    MAX_FILE_SIZE_CHARS: int = 50000
    MAX_FILES_TO_FETCH: int = 15
    MAX_TREE_LINES: int = 100

    # Timeouts
    GITHUB_TIMEOUT: int = 30
    LLM_TIMEOUT: int = 60

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000


settings = Settings()
