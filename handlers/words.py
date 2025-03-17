from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from db.mongo import db
from ai.grok import get_grok_response, WORD_SYSTEM_PROMPT
import logging
from datetime import datetime
from utils.markdown import escape_markdown

router = Router()

@router.message(Command("word"))
async def cmd_word(message: Message):
    """Обработчик команды /word {тема}"""
    try:
        # Получаем тему из сообщения
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            # Получаем текущие темы пользователя
            topics = await db.get_word_topics(message.from_user.id)
            topics_text = "\n• ".join(topics) if topics else "нет активных тем"
            
            await message.answer(
                "ℹ️ Используйте команду в формате:\n"
                "/word {тема}\n\n"
                "Это включит ежедневную отправку слов по этой теме.\n"
                "Слова будут приходить в случайное время с 9:00 до 21:00.\n\n"
                f"Ваши активные темы:\n• {topics_text}\n\n"
                "Примеры тем:\n"
                "• животные\n"
                "• еда\n"
                "• профессии\n"
                "• семья\n"
                "• путешествия\n\n"
                "Чтобы отключить уведомления по теме, используйте:\n"
                "/stopword {тема}"
            )
            return

        topic = args[1].strip().lower()
        
        # Получаем уровень пользователя и список изученных слов
        user = await db.get_user(message.from_user.id)
        level = user["language_level"] if user else "A1"
        learned_words = await db.get_learned_words(message.from_user.id)
        
        # Добавляем тему в список для ежедневных слов
        await db.add_word_topic(message.from_user.id, topic)
        
        # Если это первая тема, устанавливаем время следующего уведомления
        topics = await db.get_word_topics(message.from_user.id)
        if len(topics) == 1:
            from scheduler import generate_next_notification_time
            next_time = await generate_next_notification_time()
            await db.update_next_notification(message.from_user.id, next_time)
        
        # Генерируем первое слово сразу
        prompt = f"""Generate a Polish word related to the topic '{topic}' appropriate for {level} level student. 
The word should NOT be one of these: {', '.join(learned_words)}.
Provide the translation in Russian language and a simple example of using this word in everyday life."""
        response = await get_grok_response(prompt, WORD_SYSTEM_PROMPT)
        
        # Разбираем ответ
        try:
            word, translation, example, example_translation = response.strip().split("|")
            # Сначала подготавливаем чистый текст
            word = word.strip()
            translation = translation.strip()
            example = example.strip()
            example_translation = example_translation.strip()
            
            # Добавляем слово в список изученных
            await db.add_learned_word(message.from_user.id, word)
            
            # Форматируем сообщение со словом и скрытым переводом
            message_text = (
                f"✅ Тема *{topic}* добавлена! Теперь вы будете получать слова по этой теме каждый день.\n\n"
                f"А пока, вот ваше первое слово:\n\n"
                f"🔤 *Слово*: {word}\n"
                f"🔍 *Перевод*: ||{translation}||\n\n"
                f"📝 *Пример*: {example}\n"
                f"🔍 *Перевод*: ||{example_translation}||"
            )
            # Экранируем всё сообщение целиком один раз
            await message.answer(
                escape_markdown(message_text),
                parse_mode="MarkdownV2"
            )
        except ValueError:
            await message.answer("😔 Произошла ошибка при генерации слова. Попробуйте другую тему.")

    except Exception as e:
        logging.error(f"Error in cmd_word: {e}")
        await message.answer("😔 Произошла ошибка при получении слова. Попробуйте позже.")

@router.message(Command("stopword"))
async def cmd_stop_word(message: Message):
    """Обработчик команды /stopword {тема}"""
    try:
        # Получаем тему из сообщения
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            # Получаем текущие темы пользователя
            topics = await db.get_word_topics(message.from_user.id)
            topics_text = "\n• ".join(topics) if topics else "нет активных тем"
            
            await message.answer(
                "ℹ️ Используйте команду в формате:\n"
                "/stopword {тема}\n\n"
                "Это отключит ежедневную отправку слов по указанной теме.\n\n"
                f"Ваши активные темы:\n• {topics_text}"
            )
            return

        topic = args[1].strip().lower()
        
        # Удаляем тему из списка
        await db.remove_word_topic(message.from_user.id, topic)
        
        # Проверяем, остались ли еще темы
        topics = await db.get_word_topics(message.from_user.id)
        if not topics:
            # Если тем не осталось, отключаем уведомления
            await db.update_next_notification(message.from_user.id, None)
            await message.answer(
                "✅ Тема удалена. У вас больше нет активных тем для изучения слов.\n"
                "Используйте /word {тема}, чтобы добавить новую тему."
            )
        else:
            # Форматируем сообщение и экранируем его целиком
            message_text = f"✅ Тема *{topic}* удалена из списка."
            await message.answer(
                escape_markdown(message_text),
                parse_mode="MarkdownV2"
            )

    except Exception as e:
        logging.error(f"Error in cmd_stop_word: {e}")
        await message.answer("😔 Произошла ошибка при удалении темы. Попробуйте позже.")