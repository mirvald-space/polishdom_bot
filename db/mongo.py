from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from config import settings
from datetime import datetime
import logging

class Database:
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGODB_DB]

    async def get_user(self, user_id: int):
        return await self.db.users.find_one({"user_id": user_id})

    async def create_user(self, user_id: int, username: str):
        user_data = {
            "user_id": user_id,
            "username": username,
            "language_level": "A1",
            "learned_words": [],
            "word_topics": [],  # Темы для ежедневных слов
            "notifications_enabled": False,  # Включены ли уведомления
            "next_notification": None  # Время следующего уведомления
        }
        await self.db.users.insert_one(user_data)
        return user_data

    async def update_user_level(self, user_id: int, level: str) -> bool:
        """Update user's language level in the database."""
        try:
            result = await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"language_level": level}},
                upsert=True
            )
            return bool(result.modified_count > 0 or result.upserted_id)
        except Exception as e:
            logging.error(f"Error updating user level: {e}")
            return False

    async def add_learned_word(self, user_id: int, word: str):
        """Добавляет слово в список изученных"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"learned_words": word}}
        )

    async def get_learned_words(self, user_id: int) -> list:
        """Получает список изученных слов пользователя"""
        user = await self.get_user(user_id)
        return user.get("learned_words", []) if user else []

    async def add_word_topic(self, user_id: int, topic: str):
        """Добавляет тему для ежедневных слов"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$addToSet": {"word_topics": topic.lower()}}
        )

    async def remove_word_topic(self, user_id: int, topic: str):
        """Удаляет тему из ежедневных слов"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$pull": {"word_topics": topic.lower()}}
        )

    async def get_word_topics(self, user_id: int) -> list:
        """Получает список тем для ежедневных слов"""
        user = await self.get_user(user_id)
        return user.get("word_topics", []) if user else []

    async def update_next_notification(self, user_id: int, next_time: datetime):
        """Обновляет время следующего уведомления"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"next_notification": next_time}}
        )

    async def get_users_for_notification(self, current_time: datetime):
        """Получает пользователей, которым нужно отправить уведомление"""
        query = {
            "notifications_enabled": True,
            "next_notification": {"$lte": current_time},
            "word_topics": {"$ne": []}
        }
        logging.info(f"Getting users for notification with query: {query}")
        logging.info(f"Current time: {current_time}")
        users = await self.db.users.find(query).to_list(length=None)
        logging.info(f"Found {len(users)} users for notification")
        return users

    async def enable_notifications(self, user_id: int):
        """Включает уведомления для пользователя"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"notifications_enabled": True}}
        )

    async def disable_notifications(self, user_id: int):
        """Выключает уведомления для пользователя"""
        await self.db.users.update_one(
            {"user_id": user_id},
            {"$set": {"notifications_enabled": False}}
        )


db = Database() 