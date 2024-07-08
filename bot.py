import asyncio
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv
from loguru import logger
from pytz import timezone

from config import CHANNEL_ID  # Добавим импорт CHANNEL_ID
from config import (
    BOT_TOKEN,
    SCHEDULE_TASKS,
    TIMEZONE,
    WEBAPP_HOST,
    WEBAPP_PORT,
    WEBHOOK_PATH,
    WEBHOOK_URL,
)
from handlers.handlers import register_handlers
from handlers.interview import register_interview_handlers
from handlers.test import register_test_handlers
from keep_alive import keep_alive
from services.db import mongo  # Import MongoDB
from services.facts import send_facts
from services.phrases_sender import send_phrases
from services.quiz_sender import send_quiz

# Ensure the environment variables are loaded
load_dotenv()

# Set up logging with loguru for console output only
logger.remove()  # Remove default handler
logger.add(lambda msg: print(msg, end=""), format="{time} {level} {message}", level="DEBUG")

bot = Bot(token=BOT_TOKEN)  # type: ignore
dp = Dispatcher()

INTERVALS = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1)
}

async def register_all_handlers(dp):
    await register_handlers(dp)
    await register_interview_handlers(dp)
    await register_test_handlers(dp)
    logger.info("Handlers registered.")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)  # type: ignore
    logger.info("Successfully connected to MongoDB")
    
    for task in SCHEDULE_TASKS:
        if all(key in task for key in ['func', 'hour', 'minute', 'interval']):
            task_name = task['func']
            task_func = globals().get(task_name)
            if task_func:
                task_time = f"{task['hour']:02}:{task['minute']:02}"
                interval = INTERVALS[task['interval']]
                asyncio.create_task(schedule_task(task_func, task['hour'], task['minute'], interval, bot, CHANNEL_ID))
                logger.info(f"Scheduled {task_name} to run at {task_time} with interval {interval}")
            else:
                logger.warning(f"Function {task_name} not found.")
        else:
            logger.warning("Task is missing required keys.")

    app['keep_alive_task'] = asyncio.create_task(keep_alive(WEBHOOK_URL))

async def on_shutdown(app):
    logger.info("Running on_shutdown...")
    
    await bot.delete_webhook()
    
    if 'keep_alive_task' in app:
        app['keep_alive_task'].cancel()
        try:
            await app['keep_alive_task']
        except asyncio.CancelledError:
            logger.info("Keep-alive task cancelled")

async def handle_index(request):
    logger.info("Handling index request...")
    return web.Response(text="Hello! Everything is working!", content_type='text/html')

async def handle_ping(request):
    logger.info("Handling ping request...")
    return web.Response(text="pong")

async def main():
    logger.info(f"Current system time: {datetime.now(timezone(TIMEZONE))}")

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    app.router.add_get('/', handle_index)
    app.router.add_get('/ping', handle_ping)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    await register_all_handlers(dp)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)

    await site.start()
    logger.info("Bot started")

    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
    finally:
        logger.info("Shutting down...")
        await runner.cleanup()

async def schedule_task(task_func, hour, minute, interval, bot, channel_id):
    now = datetime.now(timezone(TIMEZONE))
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if target_time < now:
        target_time += timedelta(days=1)
    wait_time = (target_time - now).total_seconds()
    await asyncio.sleep(wait_time)
    while True:
        try:
            logger.info(f"Running task {task_func.__name__} for channel {channel_id}")
            await task_func(bot, channel_id)
        except Exception as e:
            logger.error(f"Error executing task {task_func.__name__}: {e}")
        await asyncio.sleep(interval.total_seconds())

if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(main())
