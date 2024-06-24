import json
import asyncio
from aiogram import Bot
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME

# Коллекция для хранения ID отправленных вопросов
COLLECTION_NAME = 'sent-quiz-id'

# Подключение к базе данных
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[COLLECTION_NAME]

# Функция для чтения отправленных вопросов
async def read_sent_questions():
    sent_questions = []
    async for document in collection.find({}, {'_id': 0, 'id': 1}):
        sent_questions.append(document['id'])
    return sent_questions

# Функция для записи отправленных вопросов
async def write_sent_question(question_id):
    await collection.insert_one({'id': question_id})

async def send_quiz(bot: Bot, channel_id: str, quiz_file='words/quiz.json'):
    # Чтение данных из файла quiz.json
    with open(quiz_file, 'r', encoding='utf-8') as f:
        quizzes = json.load(f)

    # Чтение отправленных вопросов
    sent_questions = await read_sent_questions()

    # Отфильтруем уже отправленные вопросы
    new_quizzes = [quiz for quiz in quizzes if quiz['id'] not in sent_questions]

    # Ограничим количество вопросов до 3
    limited_quizzes = new_quizzes[:3]

    for quiz in limited_quizzes:
        question = quiz['question']
        options = quiz['options']
        correct_option_id = options.index(quiz['answer'])

        await bot.send_poll(
            chat_id=channel_id,
            question=question,
            options=options,
            type='quiz',
            correct_option_id=correct_option_id,
            is_anonymous=True  # Сделаем опрос анонимным
        )
        
        # Добавим ID вопроса в список отправленных
        await write_sent_question(quiz['id'])
        await asyncio.sleep(5)  # Задержка между отправками викторин
