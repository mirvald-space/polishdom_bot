from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    TOKEN: str
    MONGO_URI: str
    MONGODB_DB: str = "polski"
    GROK_API_KEY: str
    CHANNEL_ID: str  # ID канала для обязательной подписки
    
    class Config:
        env_file = ".env"

settings = Settings()