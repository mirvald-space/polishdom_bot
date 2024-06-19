import json
from aiogram import Bot
import asyncio
import os

# Файл для хранения ID отправленных постов
SENT_FACTS_FILE = 'sent_facts.json'

# Функция для чтения отправленных постов
def read_sent_facts():
    if os.path.exists(SENT_FACTS_FILE):
        with open(SENT_FACTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Функция для записи отправленных постов
def write_sent_facts(sent_facts):
    with open(SENT_FACTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent_facts, f)

async def send_facts(bot: Bot, channel_id: str, facts_file='words/facts.json'):
    # Чтение данных из файла facts.json
    with open(facts_file, 'r', encoding='utf-8') as f:
        facts_data = json.load(f)

    # Чтение отправленных постов
    sent_facts = read_sent_facts()

    # Отфильтруем уже отправленные посты
    new_facts_data = [data for data in facts_data if data['id'] not in sent_facts]

    # Ограничим количество постов до 3
    limited_facts_data = new_facts_data[:3]

    # Создаем сообщение с тремя фактами
    message = "<b>🇵🇱 3 кратких факта о Польше</b>\n\n"
    for data in limited_facts_data:
        message += f"• {data['fact']}\n\n"
        # Добавим ID поста в список отправленных
        sent_facts.append(data['id'])

    if message:
        await bot.send_message(chat_id=channel_id, text=message, parse_mode='HTML')

    # Запись обновленного списка отправленных постов
    write_sent_facts(sent_facts)

# Пример использования (необходимо заполнить токеном и ID канала)
# bot = Bot(token='YOUR_BOT_TOKEN')
# asyncio.run(send_facts(bot, 'YOUR_CHANNEL_ID'))
