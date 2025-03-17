import asyncio
import logging
import os
import time
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from config import settings
from handlers import interview, test, common, words
from aiogram.types import BotCommand
from scheduler import check_notifications
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

# Определяем настройки для webhook
if os.getenv('RENDER_EXTERNAL_URL'):
    # На production используем URL от render.com
    WEBHOOK_HOST = os.getenv('RENDER_EXTERNAL_URL').rstrip('/')  # Убираем слеш в конце если есть
    WEBHOOK_PORT = 10000
    settings.IS_PRODUCTION = True
    # На production используем полный URL от render.com
    WEBHOOK_URL = f"{WEBHOOK_HOST}{settings.WEBHOOK_PATH}"
else:
    # Локально используем ngrok
    WEBHOOK_HOST = settings.WEBHOOK_HOST.rstrip('/')  # Убираем слеш в конце если есть
    WEBHOOK_PORT = settings.WEBHOOK_PORT
    # Локально добавляем https:// для ngrok
    WEBHOOK_URL = f"https://{WEBHOOK_HOST}{settings.WEBHOOK_PATH}"

# Инициализация бота и диспетчера
bot = Bot(token=settings.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Логируем настройки при запуске
logger.info(f"Starting bot with settings:")
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
dp.include_router(words.router)

# Список команд бота
commands = [
    BotCommand(command="start", description="Начать работу с ботом"),
    BotCommand(command="test", description="Пройти тест уровень языка"),
    BotCommand(command="interview", description="Тренажер интервью на карту поляка"),
    BotCommand(command="word", description="Подписаться на слова по теме"),
    BotCommand(command="stopword", description="Отписаться от слов по теме"),
]

async def on_startup(bot: Bot):
    # Устанавливаем вебхук
    await bot.set_webhook(url=WEBHOOK_URL)
    logger.info(f"Webhook set to URL: {WEBHOOK_URL}")
    
    # Регистрация команд бота
    await bot.set_my_commands(commands)
    logger.info("Bot commands registered")
    
    # Запускаем планировщик уведомлений в отдельной задаче
    asyncio.create_task(check_notifications(bot))
    logger.info("Notification scheduler started")

async def on_shutdown(bot: Bot):
    # Удаляем вебхук при выключении
    await bot.delete_webhook()
    logger.info("Webhook removed")

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
        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        ).register(app, path=settings.WEBHOOK_PATH)
        
        # Настраиваем хуки запуска и остановки
        app.on_startup.append(lambda app: on_startup(bot))
        app.on_shutdown.append(lambda app: on_shutdown(bot))
        
        # Добавляем endpoints для мониторинга
        app.router.add_get('/', health_check)  # Полный health check
        app.router.add_get('/ping', lambda r: web.Response(text='pong'))  # Простой пинг

        # Запускаем веб-сервер
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(
            runner,
            host='0.0.0.0',  # Слушаем все интерфейсы
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
    asyncio.run(main())