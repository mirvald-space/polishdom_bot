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
            "language_level": "A1"
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




db = Database() 