from aiogram import types, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from services.user_service import is_new_user, add_new_user

async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username

    if await is_new_user(user_id):
        await add_new_user(user_id, username)
        await message.answer(
            "🎉<b>Добро пожаловать!<b>\nРад видеть вас впервые. Этот бот поможет вам проверить уровень языка и подготовится к Карте Поляка.\nСледите за новостями в нашем канале <b>@polishdom<b>", parse_mode='HTML'
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await message.answer("<b>Привет!👋</b> \n Я помогу проверить твой уровень языка или подготовится к Карте Поляка.\n\n Выбери нужный раздел:👇", reply_markup=keyboard, parse_mode='HTML')

async def status_command(message: types.Message):
    await message.answer("<b>Все процессы запущены!</b>", parse_mode='HTML')

async def unknown_command(message: types.Message):
    await message.answer("Извините, я не понимаю эту команду. Пожалуйста, используйте /start или /status.")

async def register_handlers(dp: Dispatcher):
    dp.message.register(start_command, Command(commands=["start"]))
    dp.message.register(status_command, Command(commands=["status"]))
    dp.message.register(unknown_command)
