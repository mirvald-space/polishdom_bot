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
from services.facts_service import send_facts
from services.phrases_service import send_phrases
from services.movies_scheduler_service import send_movies
import schedule
from services.db import mongo  # Імпорт MongoDB

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
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger(__name__)

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
        logger.info("Successfully connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")

    # Schedule the tasks
    schedule.every().day.at("10:00").do(run_async_job, send_facts)
    schedule.every().day.at("12:00").do(run_async_job, send_phrases)
    schedule.every().day.at("14:00").do(run_async_job, send_movies)
    
    next_run_facts = kyiv_time(10, 0)
    next_run_phrases = kyiv_time(12, 0)
    next_run_movies = kyiv_time(14, 0)
    logger.info(f"Facts scheduled for 10:00 Kyiv time (next run: {next_run_facts})")
    logger.info(f"Phrases scheduled for 12:00 Kyiv time (next run: {next_run_phrases})")
    logger.info(f"Movies scheduled for 14:00 Kyiv time (next run: {next_run_movies})")

def run_async_job(coroutine_func):
    logger.info(f"Starting async job: {coroutine_func.__name__}")
    asyncio.create_task(coroutine_func(bot))

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
    logger.info(f"Current system time: {datetime.now(KYIV_TZ)}")

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

    logger.info(f"Starting web application on {WEBAPP_HOST}:{WEBAPP_PORT}")

    asyncio.create_task(scheduler())

    await stop_event.wait()

if __name__ == "__main__":
    asyncio.run(main())
