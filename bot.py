import asyncio
import logging
import os
import time
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import ClientSession, web
from dotenv import load_dotenv
from pytz import timezone, utc

from config import (
    BOT_TOKEN,
    CHANNEL_ID,
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("Setting up the bot...")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def register_all_handlers(dp):
    print("Registering handlers...")
    await register_handlers(dp)
    await register_interview_handlers(dp)
    await register_test_handlers(dp)
    print("Handlers registered.")


async def on_startup(app):
    print("Running on_startup...")
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Successfully connected to MongoDB")
    print(f"SCHEDULE_TASKS: {SCHEDULE_TASKS}")
    for task in SCHEDULE_TASKS:
        if 'func' in task and 'hour' in task and 'minute' in task and 'interval' in task:
            task_name = task['func']
            task_time = f"{task['hour']:02}:{task['minute']:02}"
            logger.info(f"Запланировано {task_name} работать на {
                        task_time} with interval {task['interval']}")
            print(f"Scheduled {task_name} to run at {
                  task_time} with interval {task['interval']}")
        else:
            logger.warning("Task is missing required keys.")
            print("Task is missing required keys.")
    # Start keep_alive task
    app['keep_alive_task'] = asyncio.create_task(keep_alive(WEBHOOK_URL))


async def on_shutdown(app):
    print("Running on_shutdown...")
    # Delete webhook
    await bot.delete_webhook()
    # Stop background tasks
    if 'keep_alive_task' in app:
        app['keep_alive_task'].cancel()
        try:
            await app['keep_alive_task']
        except asyncio.CancelledError:
            logger.info("Keep-alive task cancelled")
            print("Keep-alive task cancelled")


async def handle_index(request):
    print("Handling index request...")
    return web.Response(text="Hello! Everything is working!", content_type='text/html')


async def handle_ping(request):
    print("Handling ping request...")
    return web.Response(text="pong")


async def main():
    print("Running main function...")
    logger.info(f"Current system time: {datetime.now(timezone(TIMEZONE))}")

    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    app.router.add_get('/', handle_index)
    app.router.add_get('/ping', handle_ping)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(
        app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    await register_all_handlers(dp)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=WEBAPP_HOST, port=WEBAPP_PORT)

    await site.start()
    logger.info("Bot started")
    print("Bot started")

    try:
        while True:
            await asyncio.sleep(3600)  # Sleep for an hour
    except asyncio.CancelledError:
        logger.info("Main task cancelled")
        print("Main task cancelled")
    finally:
        logger.info("Shutting down...")
        print("Shutting down...")
        await runner.cleanup()

if __name__ == "__main__":
    print("Starting bot.py script...")
    asyncio.run(main())
