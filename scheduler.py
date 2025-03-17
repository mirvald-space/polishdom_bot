import asyncio
import logging
from datetime import datetime, timedelta
import random
from db.mongo import db
from ai.grok import get_grok_response, WORD_SYSTEM_PROMPT
from handlers.words import escape_markdown

async def generate_next_notification_time():
    """Генерирует следующее время уведомления (с 6:00 до 21:00)"""
    now = datetime.now()
    
    # Если сейчас позже 21:00, переходим на следующий день
    if now.hour >= 21:
        now += timedelta(days=1)
        now = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # Если сейчас раньше 6:00, устанавливаем время на 6:00
    elif now.hour < 6:
        now = now.replace(hour=6, minute=0, second=0, microsecond=0)
    
    # Генерируем случайное время в диапазоне от текущего до 21:00
    max_hour = 21
    current_hour = now.hour
    random_hour = random.randint(current_hour, max_hour)
    random_minute = random.randint(0, 59)
    
    next_time = now.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
    return next_time

async def send_daily_word(bot, user_id: int, topic: str):
    """Отправляет ежедневное слово пользователю"""
    try:
        # Получаем уровень пользователя и список изученных слов
        user = await db.get_user(user_id)
        level = user.get("language_level", "A1") if user else "A1"
        learned_words = await db.get_learned_words(user_id)
        
        # Генерируем слово с помощью Grok
        prompt = f"""Generate a Polish word related to the topic '{topic}' appropriate for {level} level student. 
The word should NOT be one of these: {', '.join(learned_words)}.
Provide the translation in Russian language and a simple example of using this word in everyday life."""
        response = await get_grok_response(prompt, WORD_SYSTEM_PROMPT)
        
        # Разбираем ответ
        word, translation, example, example_translation = response.strip().split("|")
        
        # Экранируем специальные символы для MarkdownV2
        topic_escaped = escape_markdown(topic)
        word_escaped = escape_markdown(word.strip())
        translation_escaped = escape_markdown(translation.strip())
        example_escaped = escape_markdown(example.strip())
        example_translation_escaped = escape_markdown(example_translation.strip())
        
        # Добавляем слово в список изученных
        await db.add_learned_word(user_id, word.strip())
        
        # Отправляем сообщение
        await bot.send_message(
            user_id,
            f"🎯 *Ваше ежедневное слово*\n\n"
            f"📖 *Тема*: {topic_escaped}\n"
            f"🔤 *Слово*: {word_escaped}\n"
            f"🔍 *Перевод*: ||{translation_escaped}||\n\n"
            f"📝 *Пример*: {example_escaped}\n"
            f"🔍 *Перевод*: ||{example_translation_escaped}||",
            parse_mode="MarkdownV2"
        )
        
        # Генерируем следующее время уведомления
        next_time = await generate_next_notification_time()
        await db.update_next_notification(user_id, next_time)
        
    except Exception as e:
        logging.error(f"Error sending daily word to user {user_id}: {e}")

async def check_notifications(bot):
    """Проверяет и отправляет уведомления пользователям"""
    while True:
        try:
            current_time = datetime.now()
            logging.info(f"Checking notifications at {current_time}")
            users = await db.get_users_for_notification(current_time)
            logging.info(f"Found {len(users)} users for notification")
            
            for user in users:
                # Выбираем случайную тему из списка тем пользователя
                topics = user.get("word_topics", [])
                logging.info(f"User {user['user_id']} has topics: {topics}")
                if topics:
                    topic = random.choice(topics)
                    logging.info(f"Selected topic '{topic}' for user {user['user_id']}")
                    await send_daily_word(bot, user["user_id"], topic)
                else:
                    logging.warning(f"User {user['user_id']} has no topics")
            
            # Проверяем каждую минуту
            await asyncio.sleep(60)
            
        except Exception as e:
            logging.error(f"Error in notification checker: {e}")
            await asyncio.sleep(60)  # В случае ошибки ждем минуту перед следующей попыткой 