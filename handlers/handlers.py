import logging
import os

from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv

from services.user_service import add_new_user, is_new_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
load_dotenv()
ALLOWED_CHAT_ID = os.getenv('ALLOWED_CHAT_ID')

# Проверка, что переменная окружения задана
if ALLOWED_CHAT_ID is not None:
    try:
        ALLOWED_CHAT_ID = int(ALLOWED_CHAT_ID)
    except ValueError:
        raise ValueError("Переменная окружения ALLOWED_CHAT_ID должна быть целым числом")
else:
    raise ValueError("Переменная окружения ALLOWED_CHAT_ID не задана")

async def delete_invite_message(message: types.Message):
    logging.info("Called delete_invite_message")
    if message.chat.id == ALLOWED_CHAT_ID:
        if message.new_chat_members or message.left_chat_member:
            await message.delete()

async def start_command(message: Message):
    logging.info("Called start_command")
    user_id = message.from_user.id
    username = message.from_user.username
    if await is_new_user(user_id):
        logging.info(f"New user detected: {username} (ID: {user_id})")
        await add_new_user(user_id, username)
        await message.answer(
            "🎉<b>Добро пожаловать!</b>\nРад видеть вас впервые. Этот бот поможет вам проверить уровень языка и подготовиться к Карте Поляка.\nСледите за новостями в нашем канале <b>@polishdom</b>", 
            parse_mode='HTML'
        )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await message.answer("<b>Привет!👋</b> \n Я помогу проверить твой уровень языка или подготовиться к Карте Поляка.\n\n Выбери нужный раздел:👇", reply_markup=keyboard, parse_mode='HTML')

async def status_command(message: types.Message):
    logging.info("Called status_command")
    await message.answer("<b>Все процессы запущены!</b>", parse_mode='HTML')

async def unknown_command(message: types.Message):
    logging.info("Called unknown_command")
    if message.text and message.text.startswith('/'):
        await message.answer("Извините, я не понимаю эту команду. Пожалуйста, используйте /start или /status.")

async def register_handlers(dp: Dispatcher):
    # Регистрируем обработчики команд
    dp.message.register(start_command, Command(commands=["start"]))
    dp.message.register(status_command, Command(commands=["status"]))
    dp.message.register(unknown_command, lambda message: message.text and message.text.startswith('/'))

    # Регистрируем обработчик удаления сервисных сообщений последним
    dp.message.register(delete_invite_message)
