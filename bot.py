import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import register_handlers
from services.scheduler_service import scheduler, send_scheduled_message
from aiogram.client.bot import DefaultBotProperties
from services.db import mongo  # Правильный импорт

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Запуск бота...")
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Проверка подключения к MongoDB
    logger.info("Подключение к MongoDB...")
    try:
        await mongo.client.admin.command('ping')
        logger.info("Подключение к MongoDB успешно")
    except Exception as e:
        logger.error(f"Ошибка подключения к MongoDB: {e}")
        return

    await register_handlers(dp)

    # Настройка планировщика задач
    scheduler.add_job(send_scheduled_message, "cron", day_of_week='mon,wed', hour=8, minute=00, args=[bot, 'phrases'])
    scheduler.add_job(send_scheduled_message, "cron", day_of_week='fri', hour=16, minute=00, args=[bot, 'movies'])
    scheduler.start()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    print(f"Loaded BOT_TOKEN: {BOT_TOKEN}")  # Проверка токена
    asyncio.run(main())
