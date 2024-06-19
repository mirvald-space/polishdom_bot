import json
from aiogram import Bot
import asyncio
import os

# Файл для хранения ID отправленных постов
SENT_POSTS_FILE = 'sent_posts.json'

# Функция для чтения отправленных постов
def read_sent_posts():
    if os.path.exists(SENT_POSTS_FILE):
        with open(SENT_POSTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Функция для записи отправленных постов
def write_sent_posts(sent_posts):
    with open(SENT_POSTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent_posts, f)

async def send_phrases(bot: Bot, channel_id: str, phrases_file='words/phrases.json'):
    # Чтение данных из файла phrases.json
    with open(phrases_file, 'r', encoding='utf-8') as f:
        phrases_data = json.load(f)

    # Чтение отправленных постов
    sent_posts = read_sent_posts()

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
        sent_posts.append(data['id'])
        await asyncio.sleep(5)  # Задержка между отправками постов, если их больше одного

    # Запись обновленного списка отправленных постов
    write_sent_posts(sent_posts)
