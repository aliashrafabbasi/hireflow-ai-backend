from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):
    APP_NAME: str = "HireFlow AI Backend"
    APP_VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"

    DEBUG: bool = True

    DATABASE_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    GROQ_API_KEY: str
    # Groq retired llama-3.3-70b-versatile on 2026-08-16; gpt-oss-120b is the replacement.
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # Visible browser RPA (n8n email → Playwright on this machine)
    RPA_ENABLED: bool = True
    HF_EMAIL: str | None = None
    HF_PASSWORD: str | None = None
    RPA_UI_EMAIL: str | None = None
    RPA_UI_PASSWORD: str | None = None
    HF_BASE_URL: str = "http://localhost:3000"
    SLACK_CHANNEL_URL: str | None = None
    RPA_SLOW_MO_MS: int = 120
    RPA_HEADLESS: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()