import re
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
import logging
from ai.openrouter import get_ai_response, TEST_SYSTEM_PROMPT
from datetime import datetime
from states.test import TestStates
from utils.markdown import escape_markdown
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router()
router.message.filter(F.chat.type == "private")

# Константы для работы с уроками
TEACHER_USERNAME = "katarzyna11"

# Единое открытое задание
OPEN_TASK = "Opowiedz o sobie i o tym, co lubisz robić. Napisz tyle, ile możesz po polsku."
FALLBACK_TASK = "Если ты совсем не знаешь польский, напиши об этом по-русски и расскажи, почему хочешь его выучить."

def get_test_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить тест")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Начать тест")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_test_keyboard()
        )
        return
        
    await message.answer(
        "📝 Тест уровня польского языка\n\n"
        "Я предложу вам один вопрос, который поможет определить ваш уровень владения польским. "
        "На его основе составлю персонализированный план обучения на месяц.",
        reply_markup=get_start_keyboard()
    )

@router.message(F.text == "📝 Начать тест")
@router.message(Command("start_test"))
async def start_test(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_test_keyboard()
        )
        return
    
    await state.set_state(TestStates.waiting_answer)
    await state.update_data(
        start_time=datetime.utcnow()
    )
    
    await message.answer(
        f"{OPEN_TASK}\n\n{FALLBACK_TASK}",
        reply_markup=get_test_keyboard()
    )

@router.message(F.text == "❌ Отменить тест")
@router.message(Command("cancel_test"))
async def cancel_test(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        await state.clear()
        await message.answer(
            "✅ Тест отменен.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "У вас нет активного теста.",
            reply_markup=ReplyKeyboardRemove()
        )

@router.message(StateFilter(TestStates.waiting_answer), ~F.text.startswith("/"), ~F.text.startswith("❌"))
async def handle_answer(message: Message, state: FSMContext):
    if not message.text or message.text.strip() == "":
        await message.answer("Пожалуйста, ответьте на задание.")
        return
    
    user_response = message.text.strip()
    
    # Анализируем ответ и создаем план
    await message.answer("🔄 Анализирую ваш ответ и создаю персонализированный план обучения...")
    
    level = await determine_level(user_response)
    await create_learning_plan(message, state, user_response, level)


async def determine_level(text):
    # Определяем уровень на основе текста пользователя
    prompt = (
        "Как опытный преподаватель польского языка, определи уровень владения языком по шкале CEFR (A0, A1, A2, B1, B2, C1, C2) "
        "на основе следующего текста от ученика:\n\n"
        f"{text}\n\n"
        "Если текст написан на русском - это уровень A0. "
        "Анализируй текст по таким критериям: словарный запас, грамматическая сложность, наличие ошибок, "
        "структура предложений, использование времен.\n\n"
        "Верни только код уровня (A0, A1, A2, B1, B2, C1, C2) без пояснений."
    )
    
    try:
        result = await get_ai_response(prompt, TEST_SYSTEM_PROMPT)
        # Извлекаем уровень из ответа
        level_match = re.search(r'(A[0-2]|B1|B2|C1|C2)', result)
        if level_match:
            return level_match.group(0)
        return "A1"  # По умолчанию A1
    except Exception as e:
        logging.error(f"Error determining level: {e}")
        return "A1"  # По умолчанию A1 при ошибке

async def create_learning_plan(message, state, user_response, level):
    # Короткий маркетинговый промпт для привлечения учеников
    summary_prompt = (
        "Ты - это я, Катя, репетитор польского языка. Напиши короткое персональное сообщение ученику после теста. "
        f"Ученик показал уровень {level}. Вот его ответ:\n\n"
        f"\"{user_response}\"\n\n"
        "Мой стиль: дружелюбный, личный, с эмодзи, на 'ты'. "
        "ВАЖНО: Сообщение должно быть коротким (максимум 150 слов) и мотивирующим!\n\n"
        "Структура сообщения:\n"
        "1. Приветствие: 'Привет! Это Катя 👋'\n"
        f"2. Краткая оценка уровня {level} с одной похвалой\n"
        "3. Одна главная проблема, которую я помогу решить\n"
        "4. Краткий призыв: 'Давай поработаем вместе! За месяц занятий ты сможешь [конкретный результат]'\n"
        "5. Завершение: 'Жду тебя на занятии! Твой репетитор, Катя 💫'\n\n"
        "Пиши лично, тепло, без лишних деталей. Цель - заинтересовать и мотивировать к занятиям."
    )
    
    try:
        plan = await get_ai_response(summary_prompt, TEST_SYSTEM_PROMPT)
        if not plan:
            raise ValueError("Пустой ответ от API")
            
        escaped_plan = escape_markdown(plan)
        
        # Сохраняем данные в базу
        # В функции create_learning_plan заменить блок сохранения в базу данных:

        try:
            from db.mongo import db
            
            # Сохраняем уровень пользователя в профиле
            await db.update_user_level(message.from_user.id, level)
            logging.info(f"Updated user {message.from_user.id} language level to {level}")
            
            # Создаем новую коллекцию для хранения результатов тестов, если её ещё нет
            if "test_results" not in await db.db.list_collection_names():
                await db.db.create_collection("test_results")
            
            # Формируем запись для сохранения
            test_data = {
                "user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "timestamp": datetime.utcnow(),
                "language_level": level,
                "user_response": user_response,
                "analysis": plan
            }
            
            # Проверяем существование предыдущей записи и обновляем её
            existing_record = await db.db.test_results.find_one({"user_id": message.from_user.id})
            if existing_record:
                # Обновляем существующую запись
                await db.db.test_results.update_one(
                    {"user_id": message.from_user.id},
                    {"$set": test_data}
                )
                logging.info(f"Updated existing test results for user {message.from_user.id}")
            else:
                # Создаем новую запись если предыдущей не было
                await db.db.test_results.insert_one(test_data)
                logging.info(f"Created new test results for user {message.from_user.id}")
            
        except Exception as db_error:
            # Логируем ошибку, но продолжаем работу
            logging.error(f"Error saving test results to database: {db_error}")
        
        # Очищаем состояние
        await state.clear()
        
        # Отправляем результат
        await message.answer(
            f"📝 Твой персонализированный план обучения польскому:\n\n{escaped_plan}",
            parse_mode="MarkdownV2",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Добавляем кнопку записи на урок
        lesson_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🎓 Записаться со скидкой 20%", url=f"https://t.me/{TEACHER_USERNAME}")]
            ]
        )
        
        await message.answer(
            "Нажми на кнопку ниже, чтобы записаться на урок и получить скидку 20% как новый ученик!👇",
            reply_markup=lesson_keyboard
        )
        
    except Exception as e:
        logging.error(f"Error creating learning plan: {e}")
        await message.answer(
            "Произошла ошибка при создании плана обучения. Пожалуйста, попробуйте позже.",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

# Обработчик для команд во время теста
@router.message(StateFilter(TestStates.waiting_answer), F.text.startswith("/"))
async def block_commands(message: Message):
    if message.text not in ["/cancel_test", "/info"]:
        await message.answer(
            "⚠️ Вы сейчас проходите тест. Команды недоступны.\n"
            "Завершите тест или нажмите '❌ Отменить тест'."
        )