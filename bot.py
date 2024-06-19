import os
import time
import logging
import asyncio
from datetime import datetime, timedelta
from pytz import timezone, utc
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN, WEBHOOK_URL, WEBHOOK_PATH, WEBAPP_HOST, WEBAPP_PORT
from handlers import register_handlers
from services.facts import send_facts
from services.movies_scheduler_service import send_movies
from services.quiz_sender import send_quiz
from services.phrases_sender import send_phrases
import schedule
from services.db import mongo  # Імпорт MongoDB
from dotenv import load_dotenv

# Загрузка конфигурации из .env файла
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Ensure the environment variable TZ is set
os.environ['TZ'] = 'Europe/Kiev'
time.tzset()

# Timezone for Kyiv
KYIV_TZ = timezone('Europe/Kiev')

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

# Configure logging with Kyiv timezone formatter
formatter = KyivTimezoneFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

# Initialize the bot with the token from the config file
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot=bot)

stop_event = asyncio.Event()

def kyiv_time(hour, minute):
    """
    Returns the next datetime at the specified hour and minute in the Kyiv timezone.
    """
    now = datetime.now(KYIV_TZ)
    future = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if future < now:
        future += timedelta(days=1)
    return future

async def on_startup(app):
    # Set up webhook
    await bot.set_webhook(WEBHOOK_URL)

    # Register handlers
    await register_handlers(dp)

    # Test MongoDB connection
    try:
        await mongo.client.server_info()
        logger.info("Успешное подключение к MongoDB")
    except Exception as e:
        logger.error(f"Не удалось подключиться к MongoDB: {e}")

    # Schedule the tasks
    schedule.every().day.at("09:00").do(run_async_job, send_quiz, bot, CHANNEL_ID)
    schedule.every().day.at("17:00").do(run_async_job, send_quiz, bot, CHANNEL_ID)
    schedule.every().day.at("12:00").do(run_async_job, send_phrases, bot, CHANNEL_ID)
    schedule.every().wednesday.at("15:00").do(run_async_job, send_facts, bot, CHANNEL_ID)
    schedule.every().saturday.at("17:00").do(run_async_job, send_movies)
    
    next_run_quiz_morning = kyiv_time(9, 0)
    next_run_quiz_evening = kyiv_time(17, 0)
    next_run_phrases = kyiv_time(12, 0)
    next_run_facts = kyiv_time(15, 0)
    next_run_movies = kyiv_time(17, 0)

    logger.info(f"Викторина 09:00 - 17:00 каждый день (следующий пост: {next_run_quiz_morning} и {next_run_quiz_evening})")
    logger.info(f"Фразы 12:00 каждый день (следующий запуск: {next_run_phrases})")
    logger.info(f"Факты 15:00 в среду (следующий запуск: {next_run_facts})")
    logger.info(f"Фильмы 17:00 в субботу (следующий запуск: {next_run_movies})")

def run_async_job(coroutine_func, *args):
    logger.info(f"Запуск асинхронного задания: {coroutine_func.__name__}")
    asyncio.create_task(coroutine_func(*args))

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

async def scheduler():
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

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

    # logger.info(f"Запуск веб-приложения на {WEBAPP_HOST}:{WEBAPP_PORT}")

    asyncio.create_task(scheduler())

    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
