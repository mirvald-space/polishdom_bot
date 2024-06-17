import asyncio
import logging
import pytz
import signal
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiohttp import web
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

async def on_startup(app):
    await bot.set_webhook(config.WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()
    await bot.session.close()
    scheduler.shutdown()

async def handle_update(request):
    try:
        update = types.Update(**await request.json())
        await dp.process_update(update)
        return web.Response(status=200)
    except Exception as e:
        logger.error(f"Failed to process update - {e}")
        return web.Response(status=500)

async def main():
    global bot, dp, scheduler
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

    # Setup web application
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.router.add_post(f"/{config.WEBHOOK_PATH}", handle_update)

    return app

if __name__ == "__main__":
    logger.info(f"Бот запущен: {config.BOT_TOKEN}")
    try:
        web.run_app(main(), host="0.0.0.0", port=config.WEBHOOK_PORT)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
