import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import register_handlers
from services.phrases_scheduler_service import phrases_scheduler, send_phrases
from services.movies_scheduler_service import movies_scheduler, send_movies
from aiogram.client.bot import DefaultBotProperties

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await register_handlers(dp)

    # Start the schedulers
    phrases_scheduler.add_job(send_phrases, "cron", day_of_week='mon', hour=13, minute=37, args=[bot])
    movies_scheduler.add_job(send_movies, "cron", day_of_week='fri', hour=14, minute=00, args=[bot])
    phrases_scheduler.start()
    movies_scheduler.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    print(f"Loaded BOT_TOKEN: {BOT_TOKEN}")  # Check the token
    asyncio.run(main())
