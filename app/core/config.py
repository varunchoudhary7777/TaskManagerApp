from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url:str
    test_database_url: str|None =None
    jwt_secret_key:str
    jwt_algorithm:str = "HS256"
    refresh_token_expire_days: int = 7

    email_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None =  None
    access_token_expire_minutes:int=30

    redis_url: str = "redis://localhost:6379/0"
    cache_enabled: bool = False
    cache_ttl_seconds: int = 60

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str= "redis://localhost:6379/2"


    upload_directory: str = "uploads"
    max_upload_size_bytes: int = 10 * 1024 * 1024 # 10 MB

    model_config=SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings=Settings()