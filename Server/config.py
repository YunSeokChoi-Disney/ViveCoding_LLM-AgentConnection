from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    LLAMA_SERVER_URL: str = "http://127.0.0.1:8080"
    LLAMA_REQUEST_TIMEOUT_SECONDS: float = 60.0
    NPC_MAX_HISTORY_TURNS: int = 20


settings = Settings()
