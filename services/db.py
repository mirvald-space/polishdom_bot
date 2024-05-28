from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME

class MongoDB:
    def __init__(self, uri: str, db_name: str):
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.users = self.db['users']  # Коллекция users для отслеживания новых пользователей
        self.language_level = self.db['languageLevel']  # Коллекция languageLevel для тестов уровня языка
        self.collection = self.db['kartaPolaka']  # Коллекция kartaPolaka

mongo = MongoDB(MONGO_URI, MONGO_DB_NAME)
