import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from handlers import interview, test, common, words
from aiogram.types import BotCommand
from scheduler import check_notifications
from utils.subscription import SubscriptionCheckMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=settings.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Логируем настройки при запуске
logger.info(f"Starting bot with settings:")
logger.info(f"CHANNEL_ID: {settings.CHANNEL_ID}")

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

async def main():
    try:
        # Проверяем доступ к каналу при запуске
        logger.info("Checking channel access...")
        try:
            chat = await bot.get_chat(settings.CHANNEL_ID)
            logger.info(f"Successfully connected to channel: {chat.title}")
            logger.info(f"Channel type: {chat.type}")
            logger.info(f"Channel username: {chat.username}")
            
            bot_me = await bot.me()
            bot_member = await bot.get_chat_member(settings.CHANNEL_ID, bot_me.id)
            logger.info(f"Bot ID: {bot_me.id}")
            logger.info(f"Bot username: {bot_me.username}")
            logger.info(f"Bot status in channel: {bot_member.status}")
            
            if bot_member.status not in ["administrator", "creator"]:
                logger.error("Bot is not an administrator in the channel!")
                logger.error("Please add the bot as an administrator to the channel")
                return
        except Exception as e:
            logger.error(f"Failed to access channel: {e}")
            logger.error("Please check that:")
            logger.error("1. The channel ID is correct")
            logger.error("2. The bot is added to the channel")
            logger.error("3. The bot has admin rights in the channel")
            return
        
        # Регистрация команд бота
        await bot.set_my_commands(commands)
        logger.info("Bot commands registered")
        
        # Запускаем планировщик уведомлений в отдельной задаче
        asyncio.create_task(check_notifications(bot))
        logger.info("Notification scheduler started")
        
        # Запуск бота
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during bot startup: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())