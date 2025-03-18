from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from db.mongo import db
from config import settings
from utils.subscription import check_subscription, get_subscription_keyboard


router = Router()

# Обработчик нажатия на кнопку проверки подписки
# Обработчик нажатия на кнопку проверки подписки уже реализован в middleware
# Этот обработчик оставлен для обратной совместимости
@router.callback_query(F.data == "check_subscription")
async def process_subscription_check(callback: CallbackQuery):
    # Обработка будет выполнена в middleware
    pass

@router.message(Command("start"))
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.create_user(message.from_user.id, message.from_user.username)
    
    # Проверяем подписку пользователя
    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    
    welcome_text = (
        "👋 Привет! Я бот для подготовки к польскому языку.\n\n"
        "Я помогу тебе:\n"
        "• Подготовиться к карте поляка\n"
        "• Узнать свой уровень и получить план обучения\n"
        "• Улучшить навыки общения\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
         "/interview - Подготовка к интервью\n"
            "/test - Узнать свой уровень и получить план обучения\n"
            "/word - Подписаться на слова по теме\n"
            "/stopword - Отписаться от слов по теме\n"
    )
    
    if not is_subscribed:
        welcome_text += (
            "\n⚠️ Для доступа ко всем функциям бота необходимо подписаться на наш канал:\n"
            "• /interview - Подготовка к интервью на карту поляка\n"
            "• /test - Узнать свой уровень и получить план обучения\n"
            "• /word - Подписаться на слова по теме\n"
            "• /stopword - Отписаться от слов по теме\n"
        )
        keyboard = get_subscription_keyboard()
        await message.answer(welcome_text, reply_markup=keyboard)
    else:
        await message.answer(welcome_text)



@router.message(Command("channel"))
async def cmd_channel(message: Message):
    """Обработчик команды /channel - отправляет ссылку на канал"""
    # Проверяем, подписан ли пользователь
    is_subscribed = await check_subscription(message.bot, message.from_user.id)
    
    if is_subscribed:
        await message.answer(
            "✅ Вы уже подписаны на наш канал! Используйте команды бота:\n\n"
            "/start - Начать работу с ботом\n"
            "/test - Начать тест уровня языка\n"
            "/interview - Подготовка к интервью\n"
            "/word - Подписаться на слова по теме\n"
            "/stopword - Отписаться от слов по теме"
        )
    else:
        # Используем клавиатуру с кнопкой проверки подписки
        keyboard = get_subscription_keyboard()
        
        await message.answer(
            "👋 Добро пожаловать! Для использования бота необходимо подписаться на наш канал.\n\n"
            "1️⃣ Нажмите кнопку «Подписаться на канал»\n"
            "2️⃣ Подпишитесь на канал\n"
            "3️⃣ Вернитесь в бот и нажмите «Проверить подписку»\n\n"
            "После подписки вам станут доступны все функции бота!",
            reply_markup=keyboard
        )