from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject, User, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from config import settings

# Функция для проверки подписки пользователя на канал
async def check_subscription(bot, user_id: int) -> bool:
    """Проверяет, подписан ли пользователь на канал"""
    try:
        # Используем числовой ID канала напрямую
        member = await bot.get_chat_member(settings.CHANNEL_ID, user_id)
        # Проверяем статус пользователя
        is_member = member.status in ["creator", "administrator", "member"]
        print(f"User {user_id} subscription status: {member.status} (is_member: {is_member})")
        return is_member
    except Exception as e:
        print(f"Ошибка при проверке подписки для user_id={user_id}: {e}")
        print(f"Используемый CHANNEL_ID: {settings.CHANNEL_ID}")
        return False

# Функция для создания клавиатуры с кнопкой подписки
def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру с кнопкой подписки на канал и кнопкой проверки подписки"""
    channel_id = settings.CHANNEL_ID
    
    # Для приватных каналов используем полный ID
    if str(channel_id).startswith('-100'):
        # Убираем -100 из начала ID и добавляем + для создания ссылки
        channel_link = f"https://t.me/polishdom"
    else:
        channel_link = f"https://t.me/polishdom"
    
    print(f"Channel ID: {channel_id}")
    print(f"Generated link: {channel_link}")
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на канал PolishDom", url=channel_link)],
        [InlineKeyboardButton(text="🔄 Проверить подписку", callback_data="check_subscription")]
    ])

# Middleware для проверки подписки на канал
class SubscriptionCheckMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id в зависимости от типа события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None

        if not user_id:
            return None

        # Проверяем подписку
        is_subscribed = await check_subscription(data["bot"], user_id)

        # Если это callback проверки подписки
        if isinstance(event, CallbackQuery) and event.data == "check_subscription":
            if is_subscribed:
                # Сначала отправляем новое сообщение
                await data["bot"].send_message(
                    chat_id=user_id,
                    text="👋 Добро пожаловать! Теперь вы можете использовать бота.\n"
                         "Отправьте /start для начала работы."
                )
                # Затем показываем уведомление
                await event.answer("✅ Доступ разрешен!", show_alert=True)
                # И только потом удаляем старое сообщение
                try:
                    await event.message.delete()
                except Exception as e:
                    print(f"Ошибка при удалении сообщения: {e}")
            else:
                await event.answer("⛔️ Вы не подписаны на канал PolishDom!", show_alert=True)
            return

        # Если пользователь не подписан
        if not is_subscribed:
            keyboard = get_subscription_keyboard()
            if isinstance(event, Message):
                # Отправляем сообщение с кнопкой подписки
                await event.answer(
                    "👋 Привет! Для использования бота необходимо подписаться на наш канал.\n\n"
                    "1️⃣ Нажмите на кнопку ниже\n"
                    "2️⃣ Подпишитесь на канал «PolishDom: Польский язык с нуля 🚀»\n"
                    "3️⃣ Вернитесь в бот и нажмите «Проверить подписку»",
                    reply_markup=keyboard
                )
            elif isinstance(event, CallbackQuery):
                # Для callback-запросов показываем всплывающее сообщение
                await event.answer("⛔️ Необходимо подписаться на канал!", show_alert=True)
                # И отправляем сообщение с кнопкой подписки
                await event.message.answer(
                    "Для использования бота необходимо подписаться на канал:",
                    reply_markup=keyboard
                )
            return None

        # Если пользователь подписан - пропускаем событие дальше
        return await handler(event, data)