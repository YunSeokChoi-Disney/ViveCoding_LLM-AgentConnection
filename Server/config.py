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

    # WhatsApp Business Cloud API (미설정 시 웹훅만 비활성, 서버는 정상 기동)
    WHATSAPP_VERIFY_TOKEN: str = ""
    WHATSAPP_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_APP_SECRET: str = ""
    WHATSAPP_LLM_URL: str = "http://127.0.0.1:8080"
    WHATSAPP_GRAPH_API_VERSION: str = "v21.0"
    WHATSAPP_MAX_HISTORY_TURNS: int = 10


settings = Settings()
