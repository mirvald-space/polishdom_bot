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
            self.scores_quiz = self.db['scores_quiz']  # Коллекция для результатов викторины
            self.questions_quiz = self.db['questions_quiz']  # Коллекция для вопросов викторины
            logging.info("Successfully connected to MongoDB")
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")

    async def save_interview_evaluation(self, user_id: int, username: str, rating: int):
        try:
            await self.interview_evaluation.insert_one({"user_id": user_id, "username": username, "rating": rating})
            logging.info("Interview evaluation saved successfully")
        except Exception as e:
            logging.error(f"Failed to save interview evaluation: {e}")

    async def update_quiz_score(self, user_id: int, username: str):
        try:
            result = await self.scores_quiz.find_one({"user_id": user_id})
            if result:
                await self.scores_quiz.update_one({"user_id": user_id}, {"$inc": {"score": 1}})
            else:
                await self.scores_quiz.insert_one({"user_id": user_id, "username": username, "score": 1})
            logging.info("Quiz score updated successfully")
        except Exception as e:
            logging.error(f"Failed to update quiz score: {e}")

    async def get_quiz_scores(self):
        try:
            scores = []
            async for user in self.scores_quiz.find().sort("score", -1):
                scores.append(user)
            return scores
        except Exception as e:
            logging.error(f"Failed to get quiz scores: {e}")
            return []

    async def get_unused_quiz_question(self):
        try:
            question = await self.questions_quiz.find_one({"used": False})
            return question
        except Exception as e:
            logging.error(f"Failed to get unused quiz question: {e}")
            return None

    async def mark_question_used(self, question_id):
        try:
            await self.questions_quiz.update_one({"_id": question_id}, {"$set": {"used": True}})
            logging.info(f"Question marked as used: {question_id}")
        except Exception as e:
            logging.error(f"Failed to mark question as used: {e}")

mongo = MongoDB(MONGO_URI, MONGO_DB_NAME)
