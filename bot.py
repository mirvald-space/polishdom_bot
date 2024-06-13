import asyncio
import logging
import pytz
import signal
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import config
from handlers import register_handlers
from services.facts_service import send_facts
from services.phrases_service import send_phrases
from services.movies_scheduler_service import send_movies
from aiogram.client.bot import DefaultBotProperties
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timezone for Kyiv
KYIV_TZ = pytz.timezone('Europe/Kiev')

async def main():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await register_handlers(dp)

    # Initialize the scheduler
    scheduler = AsyncIOScheduler(timezone=KYIV_TZ)
    
    # Start the schedulers
    scheduler.add_job(
        send_facts, 
        "cron", 
        day_of_week=config.FACTS_SCHEDULE["day_of_week"], 
        hour=config.FACTS_SCHEDULE["hour"], 
        minute=config.FACTS_SCHEDULE["minute"], 
        args=[bot]
    )
    scheduler.add_job(
        send_phrases, 
        "cron", 
        day_of_week=config.PHRASES_SCHEDULE["day_of_week"], 
        hour=config.PHRASES_SCHEDULE["hour"], 
        minute=config.PHRASES_SCHEDULE["minute"], 
        args=[bot]
    )
    scheduler.add_job(
        send_movies, 
        "cron", 
        day_of_week=config.MOVIES_SCHEDULE["day_of_week"], 
        hour=config.MOVIES_SCHEDULE["hour"], 
        minute=config.MOVIES_SCHEDULE["minute"], 
        args=[bot]
    )
    
    scheduler.start()
    logger.info("Scheduler started. Waiting for jobs to be executed...")

    # Обработка сигналов
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, loop.stop)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Failed to fetch updates - {e}")
        await asyncio.sleep(1)
    finally:
        await bot.session.close()
        scheduler.shutdown()

if __name__ == "__main__":
    logger.info(f"Бот запущен: {config.BOT_TOKEN}")
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
