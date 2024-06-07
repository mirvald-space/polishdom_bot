import asyncio
import pytz
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
import config
from handlers import register_handlers
from services.facts_service import facts_scheduler, send_facts
from services.phrases_service import send_phrases, phrases_scheduler
from services.movies_scheduler_service import movies_scheduler, send_movies
from aiogram.client.bot import DefaultBotProperties

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

    # Start the schedulers
    facts_scheduler.add_job(
        send_facts, 
        "cron", 
        day_of_week=config.FACTS_SCHEDULE["day_of_week"], 
        hour=config.FACTS_SCHEDULE["hour"], 
        minute=config.FACTS_SCHEDULE["minute"], 
        args=[bot], 
        timezone=KYIV_TZ
    )
    phrases_scheduler.add_job(
        send_phrases, 
        "cron", 
        day_of_week=config.PHRASES_SCHEDULE["day_of_week"], 
        hour=config.PHRASES_SCHEDULE["hour"], 
        minute=config.PHRASES_SCHEDULE["minute"], 
        args=[bot], 
        timezone=KYIV_TZ
    )
    movies_scheduler.add_job(
        send_movies, 
        "cron", 
        day_of_week=config.MOVIES_SCHEDULE["day_of_week"], 
        hour=config.MOVIES_SCHEDULE["hour"], 
        minute=config.MOVIES_SCHEDULE["minute"], 
        args=[bot], 
        timezone=KYIV_TZ
    )
    facts_scheduler.start()
    phrases_scheduler.start()
    movies_scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    print(f"Loaded BOT_TOKEN: {config.BOT_TOKEN}")  # Check the token
    asyncio.run(main())
