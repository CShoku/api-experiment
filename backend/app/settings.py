from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str

    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET: str | None = None

    PRESIGNED_TTL_SECONDS: int = 600
    PUBLIC_CDN_BASE: str | None = None

    OPENAI_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None
    ANTHROPIC_API_KEY: str | None = None

    JWT_SECRET: str = "dev"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
