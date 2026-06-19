from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Resume Analyser AI"
    app_version: str = "1.0.0"
    debug: bool = False
    groq_api_key: str
    database_url: str = "postgresql://postgres:postgres@localhost:5432/resume_analyser"
    secret_key: str = "your-secret-key-change-this-in-production"
    cors_origins: str = "http://localhost:3000,http://localhost:8501"
    max_upload_size_mb: int = 5

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
