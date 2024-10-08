import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from dotenv import load_dotenv

from services.user_service import add_new_user, is_new_user

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
load_dotenv()
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Проверка, что переменная окружения задана
if CHANNEL_ID is None:
    raise ValueError("Переменная окружения CHANNEL_ID не задана")

async def check_subscription(user_id: int, bot: Bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{CHANNEL_ID}", user_id=user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception as e:
        logging.error(f"Failed to check subscription status: {e}")
        return False

async def send_welcome_message(message: Message, user_id: int, username: str):
    if await is_new_user(user_id):
        logging.info(f"New user detected: {username} (ID: {user_id})")
        await add_new_user(user_id, username)
        await message.answer(
            "🎉<b>Добро пожаловать!</b>\nРад видеть вас впервые. Этот бот поможет вам проверить уровень языка и подготовиться к Карте Поляка.\nСледите за новостями в нашем канале <b>@polishdom</b>", 
            parse_mode='HTML'
        )

async def send_subscription_prompt(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подтвердить подписку", callback_data="check_subscription")],
        [InlineKeyboardButton(text="📢 Наш канал", url=f"https://t.me/{CHANNEL_ID}")]
    ])
    await message.answer("Для доступа к боту необходимо подписаться на наш канал. Пожалуйста, подтвердите подписку.", reply_markup=keyboard, parse_mode='HTML')

async def send_main_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверить уровень языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к Карте Поляка", callback_data="interview")]
    ])
    await message.answer("<b>Привет!👋</b>\nЯ помогу проверить твой уровень языка или подготовиться к Карте Поляка.\n\nВыбери нужный раздел:👇", reply_markup=keyboard, parse_mode='HTML')

async def start_command(message: Message):
    logging.info("Called start_command")
    user_id = message.from_user.id if message.from_user else None
    username = message.from_user.username if message.from_user and message.from_user.username else "Unknown"

    if user_id:
        await send_welcome_message(message, user_id, username)
        
        if await check_subscription(user_id, message.bot):
            await send_main_menu(message)
        else:
            await send_subscription_prompt(message)

async def status_command(message: types.Message):
    logging.info("Called status_command")
    await message.answer("<b>Все процессы запущены!</b>", parse_mode='HTML')

async def check_subscription_callback(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if await check_subscription(user_id, callback_query.bot):
        await callback_query.answer("Подписка подтверждена!")
        await send_main_menu(callback_query.message)
    else:
        await callback_query.answer("Подписка не подтверждена. Пожалуйста, подпишитесь на канал.")

async def register_handlers(dp: Dispatcher):
    # Регистрируем обработчики команд
    dp.message.register(start_command, Command(commands=["start"]))
    dp.message.register(status_command, Command(commands=["status"]))

    # Регистрируем обработчик коллбэков
    dp.callback_query.register(check_subscription_callback, lambda c: c.data == 'check_subscription')
