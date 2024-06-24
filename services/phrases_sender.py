import json
import asyncio
from aiogram import Bot
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME

# Коллекция для хранения ID отправленных постов
COLLECTION_NAME = 'sent-phrases-id'

# Подключение к базе данных
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[COLLECTION_NAME]

# Функция для чтения отправленных постов
async def read_sent_posts():
    sent_posts = []
    async for document in collection.find({}, {'_id': 0, 'id': 1}):
        sent_posts.append(document['id'])
    return sent_posts

# Функция для записи отправленных постов
async def write_sent_post(post_id):
    await collection.insert_one({'id': post_id})

async def send_phrases(bot: Bot, channel_id: str, phrases_file='words/phrases.json'):
    # Чтение данных из файла phrases.json
    with open(phrases_file, 'r', encoding='utf-8') as f:
        phrases_data = json.load(f)

    # Чтение отправленных постов
    sent_posts = await read_sent_posts()

    # Отфильтруем уже отправленные посты
    new_phrases_data = [data for data in phrases_data if data['id'] not in sent_posts]

    # Ограничим количество постов до 1 (если нужно больше, можно изменить это значение)
    limited_phrases_data = new_phrases_data[:1]

    for data in limited_phrases_data:
        title = data['title']
        phrases = data['phrases']

        message = f"<b>{title}</b>\n\n"
        formatted_phrases = [f"• <b>{phrase.split(' - ')[0]}</b> - {phrase.split(' - ')[1]}" for phrase in phrases]
        message += "\n".join(formatted_phrases)

        await bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')

        # Добавим ID поста в список отправленных
        await write_sent_post(data['id'])
        await asyncio.sleep(5)  # Задержка между отправками постов, если их больше одного
