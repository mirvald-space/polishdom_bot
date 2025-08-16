import asyncio
import logging
import os
import time
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.exceptions import TelegramAPIError
from config import settings
from handlers import interview, test, common
from aiogram.types import BotCommand

from utils.subscription import SubscriptionCheckMiddleware
from db.mongo import db

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Время запуска приложения
START_TIME = time.time()

# Проверяем обязательные переменные окружения
required_env_vars = {
    'TOKEN': settings.TOKEN,
    'MONGO_URI': settings.MONGO_URI,
    'CHANNEL_ID': settings.CHANNEL_ID
}

for var_name, var_value in required_env_vars.items():
    if not var_value:
        logger.error(f"Missing required environment variable: {var_name}")
        raise ValueError(f"Missing required environment variable: {var_name}")

# Определяем настройки для webhook
if os.getenv('RENDER_EXTERNAL_URL'):
    # На production используем URL от render.com
    WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL').rstrip('/')
    WEBHOOK_PORT = 10000
    settings.IS_PRODUCTION = True
    WEBHOOK_URL = f"{WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
else:
    # Локально используем ngrok
    WEBHOOK_HOST = settings.WEBHOOK_HOST.rstrip('/')
    WEBHOOK_PORT = settings.WEBHOOK_PORT
    WEBHOOK_URL = f"{WEBHOOK_HOST}{settings.WEBHOOK_PATH}"

# Инициализация бота и диспетчера
bot = Bot(token=settings.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Логируем настройки при запуске
logger.info("Starting bot with settings:")
logger.info(f"CHANNEL_ID: {settings.CHANNEL_ID}")
logger.info(f"WEBHOOK_URL: {WEBHOOK_URL}")
logger.info(f"WEBHOOK_PORT: {WEBHOOK_PORT}")
logger.info(f"Environment: {'Production' if settings.IS_PRODUCTION else 'Development'}")

# Регистрация middleware для проверки подписки на канал
dp.message.middleware(SubscriptionCheckMiddleware())
dp.callback_query.middleware(SubscriptionCheckMiddleware())

# Регистрация роутеров
dp.include_router(common.router)
dp.include_router(interview.router)
dp.include_router(test.router)

# Список команд бота
commands = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="test", description="Узнать свой уровень и получить план"),
    BotCommand(command="interview", description="Тренажер интервью на карту поляка"),
]

async def check_telegram_token():
    """Проверяет валидность токена бота"""
    try:
        bot_info = await bot.me()
        logger.info(f"Bot authorized as @{bot_info.username} (ID: {bot_info.id})")
        return True
    except TelegramAPIError as e:
        logger.error(f"Failed to authorize bot: {e}")
        return False

async def check_mongo_connection():
    """Проверяет подключение к MongoDB"""
    try:
        await db.db.command('ping')
        logger.info("Successfully connected to MongoDB")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        return False

async def on_startup(bot: Bot):
    """Действия при запуске бота"""
    try:
        # Проверяем подключение к Telegram
        if not await check_telegram_token():
            raise ValueError("Invalid Telegram token")

        # Проверяем подключение к MongoDB
        if not await check_mongo_connection():
            raise ValueError("Failed to connect to MongoDB")

        # Устанавливаем вебхук
        await bot.set_webhook(url=WEBHOOK_URL)
        logger.info(f"Webhook set to URL: {WEBHOOK_URL}")
        
        # Проверяем доступ к каналу
        try:
            chat = await bot.get_chat(settings.CHANNEL_ID)
            bot_member = await bot.get_chat_member(settings.CHANNEL_ID, (await bot.me()).id)
            if bot_member.status not in ["administrator", "creator"]:
                raise ValueError("Bot is not an administrator in the channel")
            logger.info(f"Successfully connected to channel {chat.title} (@{chat.username})")
        except TelegramAPIError as e:
            logger.error(f"Failed to access channel: {e}")
            raise ValueError(f"Failed to access channel: {e}")
        
        # Регистрация команд бота
        await bot.set_my_commands(commands)
        logger.info("Bot commands registered")
        

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

async def on_shutdown(bot: Bot):
    """Действия при остановке бота"""
    try:
        # Удаляем вебхук
        await bot.delete_webhook()
        logger.info("Webhook removed")
        
        # Закрываем соединения
        await bot.session.close()
        logger.info("Bot session closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

async def get_bot_status():
    """Проверяет статус бота через Telegram API"""
    try:
        me = await bot.me()
        return {
            "ok": True,
            "username": me.username,
            "bot_id": me.id
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

async def get_mongo_status():
    """Проверяет подключение к MongoDB"""
    try:
        # Простой ping к базе данных
        await db.db.command('ping')
        return {
            "ok": True,
            "connected": True
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

async def health_check(request):
    """Расширенный health check с информацией о состоянии сервисов"""
    try:
        # Собираем статусы всех сервисов
        mongo_status = await get_mongo_status()
        bot_status = await get_bot_status()
        
        # Вычисляем uptime
        uptime = int(time.time() - START_TIME)
        
        health_data = {
            "status": "ok" if mongo_status["ok"] and bot_status["ok"] else "error",
            "timestamp": time.time(),
            "uptime_seconds": uptime,
            "environment": "production" if settings.IS_PRODUCTION else "development",
            "services": {
                "mongodb": mongo_status,
                "telegram_bot": bot_status
            },
            "version": "1.0.0"  # Добавьте версию вашего приложения
        }
        
        # Если все сервисы работают, возвращаем 200, иначе 500
        status = 200 if health_data["status"] == "ok" else 500
        
        return web.json_response(health_data, status=status)
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return web.json_response({
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }, status=500)

async def main():
    try:
        # Создаем приложение aiohttp
        app = web.Application()
        
        # Настраиваем обработчик вебхуков
        webhook_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_handler.register(app, path=settings.WEBHOOK_PATH)
        
        # Настраиваем хуки запуска и остановки
        app.on_startup.append(lambda app: on_startup(bot))
        app.on_shutdown.append(lambda app: on_shutdown(bot))
        
        # Добавляем endpoints для мониторинга
        app.router.add_get('/', health_check)
        app.router.add_get('/ping', lambda r: web.Response(text='pong'))

        # Запускаем веб-сервер
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host='0.0.0.0',
            port=WEBHOOK_PORT
        )
        await site.start()
        
        logger.info(f"Bot started on port {WEBHOOK_PORT}")
        
        # Ждем бесконечно
        await asyncio.Event().wait()
    except Exception as e:
        logger.error(f"Error during bot startup: {e}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
