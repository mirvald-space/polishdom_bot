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
            "notifications_enabled": True,  # Включены ли уведомления
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

    async def create_session(self, user_id: int, session_type: str) -> str:
        """Создает новую сессию и возвращает её ID"""
        logging.info(f"Creating new {session_type} session for user {user_id}")
        
        # Удаляем все существующие сессии пользователя
        await self.db.sessions.delete_many({"user_id": user_id})
        logging.info(f"Deleted existing sessions for user {user_id}")
        
        current_time = datetime.utcnow()
        session = {
            "user_id": user_id,
            "session_type": session_type,
            "questions": [],
            "answers": [],
            "created_at": current_time,
            "last_activity": current_time  # Устанавливаем начальное время активности
        }
        result = await self.db.sessions.insert_one(session)
        session_id = str(result.inserted_id)
        logging.info(f"Created session with ID: {session_id}")
        return session_id

    async def get_session(self, session_id: str):
        """Получает сессию по ID"""
        try:
            logging.info(f"Getting session with ID: {session_id}")
            session = await self.db.sessions.find_one({"_id": ObjectId(session_id)})
            if session:
                logging.info(f"Found session: {session}")
            else:
                logging.warning(f"Session not found: {session_id}")
            return session
        except Exception as e:
            logging.error(f"Error getting session {session_id}: {e}")
            return None

    async def get_user_session(self, user_id: int):
        """Получает активную сессию пользователя"""
        logging.info(f"Getting active session for user {user_id}")
        session = await self.db.sessions.find_one({
            "user_id": user_id,
            "session_type": {"$in": ["interview", "test"]}
        })
        if session:
            logging.info(f"Found active session: {session}")
        else:
            logging.warning(f"No active session found for user {user_id}")
        return session

    async def update_session(self, session_id: str, question: str, answer: str):
        """Обновляет сессию, добавляя вопрос и ответ и обновляя время последней активности"""
        logging.info(f"Updating session {session_id} with question and answer")
        try:
            current_time = datetime.utcnow()
            await self.db.sessions.update_one(
                {"_id": ObjectId(session_id)},
                {
                    "$push": {
                        "questions": question,
                        "answers": answer
                    },
                    "$set": {
                        "last_activity": current_time  # Обновляем время активности только при ответе на вопрос
                    }
                }
            )
            logging.info("Session updated successfully")
        except Exception as e:
            logging.error(f"Error updating session: {e}")

    async def delete_session(self, session_id: str):
        """Удаляет сессию"""
        logging.info(f"Deleting session {session_id}")
        try:
            await self.db.sessions.delete_one({"_id": ObjectId(session_id)})
            logging.info(f"Successfully deleted session {session_id}")
        except Exception as e:
            logging.error(f"Error deleting session {session_id}: {e}")

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
        return await self.db.users.find({
            "notifications_enabled": True,
            "next_notification": {"$lte": current_time},
            "word_topics": {"$ne": []}
        }).to_list(length=None)

    async def is_session_expired(self, session_id: str, timeout_minutes: int = 30) -> bool:
        """Проверяет, истекла ли сессия"""
        try:
            session = await self.get_session(session_id)
            if not session:
                return True
            
            last_activity = session.get("last_activity")
            if not last_activity:
                return True
            
            time_passed = datetime.utcnow() - last_activity
            return time_passed.total_seconds() > (timeout_minutes * 60)
        except Exception as e:
            logging.error(f"Error checking session expiration: {e}")
            return True

    async def update_session_activity(self, session_id: str) -> bool:
        """Обновляет время последней активности сессии"""
        try:
            result = await self.db.sessions.update_one(
                {"_id": ObjectId(session_id)},
                {"$set": {"last_activity": datetime.utcnow()}}
            )
            return result.modified_count > 0
        except Exception as e:
            logging.error(f"Error updating session activity: {e}")
            return False

db = Database() 