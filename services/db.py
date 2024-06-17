import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME

class MongoDB:
    def __init__(self, uri: str, db_name: str):
        try:
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client[db_name]
            self.users = self.db['users']  # Коллекция users для отслеживания новых пользователей
            self.language_level = self.db['languageLevel']  # Коллекция languageLevel для тестов уровня языка
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")

mongo = MongoDB(MONGO_URI, MONGO_DB_NAME)
