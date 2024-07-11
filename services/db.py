import logging

from motor.motor_asyncio import AsyncIOMotorClient

from config import MONGO_DB_NAME, MONGO_URI


class MongoDB:
    def __init__(self, uri: str, db_name: str):
        try:
            self.client = AsyncIOMotorClient(uri)
            self.db = self.client[db_name]
            self.users = self.db['users']  # Коллекция users для отслеживания новых пользователей
            self.language_level = self.db['languageLevel']  # Коллекция languageLevel для тестов уровня языка
            self.interview_evaluation = self.db['interview_evaluation']  # Коллекция для оценки интервью
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")

    async def save_interview_evaluation(self, user_id: int, username: str, rating: int):
        try:
            await self.interview_evaluation.insert_one({"user_id": user_id, "username": username, "rating": rating})
            logging.info("Interview evaluation saved successfully")
        except Exception as e:
            logging.error(f"Failed to save interview evaluation: {e}")

mongo = MongoDB(MONGO_URI, MONGO_DB_NAME)
