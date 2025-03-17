from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    TOKEN: str
    MONGO_URI: str
    MONGODB_DB: str = "polski"
    GROK_API_KEY: str
    CHANNEL_ID: str  # ID канала для обязательной подписки
    
    # Webhook settings
    WEBHOOK_HOST: str = "localhost"  # Will be overridden by RENDER_EXTERNAL_URL in production
    WEBHOOK_PATH: str = "/webhook"
    WEBHOOK_PORT: int = 10000  # Port for local development
    IS_PRODUCTION: bool = False  # Will be True on render.com
    
    class Config:
        env_file = ".env"

settings = Settings()