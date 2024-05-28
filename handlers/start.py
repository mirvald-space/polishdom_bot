from aiogram import Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from services.user_service import is_new_user, add_new_user

async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if await is_new_user(user_id):
        await add_new_user(user_id, username)
        await message.answer(
            "🎉 Добро пожаловать! Рад видеть вас впервые. Этот бот поможет вам подготовиться к Карте Поляка, попрактиковаться в языке и проверить свои знания. В будущем бот поможет записаться на подачу документов. Следите за новостями в нашем канале @polishdom."
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await message.answer("Привет! Я помогу тебе подготовиться к Карте Поляка. Выбери нужный раздел:", reply_markup=keyboard)

def register_start_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command("start"))
