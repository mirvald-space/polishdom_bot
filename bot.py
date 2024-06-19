import os
import time
import logging
import asyncio
from datetime import datetime, timedelta, time as dtime
from pytz import timezone, utc
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from services.facts import send_facts
# from services.movies_scheduler_service import send_movies
from services.quiz_sender import send_quiz
from services.phrases_sender import send_phrases
from services.db import mongo  # Імпорт MongoDB
from dotenv import load_dotenv
from handlers.start import register_start_handlers
from handlers.test import register_test_handlers
from handlers.interview import register_interview_handlers

# Загрузка конфигурации из .env файла
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Ensure the environment variable TZ is set
os.environ['TZ'] = 'Europe/Kiev'
time.tzset()

# Timezone for Kyiv
KYIV_TZ = timezone('Europe/Kiev')

# Initialize the logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Custom log formatter to use Kyiv time
class KyivTimezoneFormatter(logging.Formatter):
    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=utc).astimezone(KYIV_TZ)
        return dt

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            s = dt.strftime(datefmt)
        else:
            t = dt.strftime(self.default_time_format)
            s = self.default_msec_format % (t, record.msecs)
        return s

# Configure logging with Kyiv timezone formatter if not already configured
if not logger.hasHandlers():
    formatter = KyivTimezoneFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Adding a debug statement to verify logger configuration
logger.info("Logger configured successfully")

# Initialize the bot with the token from the config file
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

stop_event = asyncio.Event()

async def schedule_task(func, hour, minute, interval='daily', day_of_week=None, *args):
    while True:
        now = datetime.now(KYIV_TZ)
        if interval == 'daily':
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now > next_run:
                next_run += timedelta(days=1)
        elif interval == 'weekly' and day_of_week is not None:
            days_ahead = (day_of_week - now.weekday() + 7) % 7
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if now > next_run:
                next_run += timedelta(weeks=1)
        else:
            raise ValueError("Invalid interval or day_of_week not provided for weekly interval")

        sleep_time = (next_run - now).total_seconds()
        logger.info(f"Scheduled {func.__name__} to run at {next_run}")
        await asyncio.sleep(sleep_time)
        await func(*args)
        await asyncio.sleep(1)  # Small sleep to prevent potential tight loop issues

async def on_startup(app):
    # Set up webhook
    await bot.set_webhook(WEBHOOK_URL)

    # Register handlers
    await register_start_handlers(dp)
    await register_test_handlers(dp)
    await register_interview_handlers(dp)

    # Test MongoDB connection
    try:
        await mongo.client.server_info()
        logger.info("Успешное подключение к MongoDB")
    except Exception as e:
        logger.error(f"Не удалось подключиться к MongoDB: {e}")

    # Schedule tasks
    asyncio.create_task(schedule_task(send_quiz, 9, 0, 'daily', bot, CHANNEL_ID))
    asyncio.create_task(schedule_task(send_quiz, 17, 0, 'daily', bot, CHANNEL_ID))
    asyncio.create_task(schedule_task(send_phrases, 12, 0, 'daily', bot, CHANNEL_ID))
    asyncio.create_task(schedule_task(send_facts, 15, 0, 'weekly', 2, bot, CHANNEL_ID))  # Wednesday
    # asyncio.create_task(schedule_task(send_movies, 00, 49, 'weekly', 3, bot))  # Saturday

@dp.message(Command("status"))
async def status_command(message: types.Message):
    await message.answer("All processes are running!")

async def on_shutdown(app):
    # Delete webhook
    await bot.delete_webhook()

    # Stop background tasks
    stop_event.set()

async def handle_index(request):
    return web.Response(text="Hello! Everything is working!", content_type='text/html')

async def main():
    logger.info(f"Текущее системное время: {datetime.now(KYIV_TZ)}")

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    # Add a route for the home page
    app.router.add_get('/', handle_index)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)
    await site.start()

    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
