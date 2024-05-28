from services.db import mongo
from bson import ObjectId

async def get_test_questions():
    questions = await mongo.language_level.aggregate([
        {"$match": {"type": "test"}},
        {"$sample": {"size": 36}}
    ]).to_list(length=36)
    return questions

async def check_test_answer(question_id, user_answer):
    question = await mongo.language_level.find_one({"_id": ObjectId(question_id)})
    return question and question.get('correct_answer') == user_answer
