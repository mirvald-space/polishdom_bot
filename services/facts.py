import json
import asyncio
from aiogram import Bot
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URI, MONGO_DB_NAME

# Коллекция для хранения ID отправленных постов
COLLECTION_NAME = 'sent-facts-id'

# Подключение к базе данных
client = AsyncIOMotorClient(MONGO_URI)
db = client[MONGO_DB_NAME]
collection = db[COLLECTION_NAME]

# Функция для чтения отправленных постов
async def read_sent_facts():
    sent_facts = []
    async for document in collection.find({}, {'_id': 0, 'id': 1}):
        sent_facts.append(document['id'])
    return sent_facts

# Функция для записи отправленных постов
async def write_sent_fact(fact_id):
    await collection.insert_one({'id': fact_id})

async def send_facts(bot: Bot, channel_id: str, facts_file='words/facts.json'):
    # Чтение данных из файла facts.json
    with open(facts_file, 'r', encoding='utf-8') as f:
        facts_data = json.load(f)

    # Чтение отправленных постов
    sent_facts = await read_sent_facts()

    # Отфильтруем уже отправленные посты
    new_facts_data = [data for data in facts_data if data['id'] not in sent_facts]

    # Ограничим количество постов до 3
    limited_facts_data = new_facts_data[:3]

    # Создаем сообщение с тремя фактами
    message = "<b>🇵🇱 3 кратких факта о Польше</b>\n\n"
    for data in limited_facts_data:
        message += f"• {data['fact']}\n\n"
        # Добавим ID поста в список отправленных
        await write_sent_fact(data['id'])

    if message:
        await bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')