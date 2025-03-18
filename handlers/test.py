import re
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
import logging
from ai.grok import get_grok_response, TEST_SYSTEM_PROMPT
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
        result = await get_grok_response(prompt, TEST_SYSTEM_PROMPT)
        # Извлекаем уровень из ответа
        level_match = re.search(r'(A[0-2]|B1|B2|C1|C2)', result)
        if level_match:
            return level_match.group(0)
        return "A1"  # По умолчанию A1
    except Exception as e:
        logging.error(f"Error determining level: {e}")
        return "A1"  # По умолчанию A1 при ошибке

async def create_learning_plan(message, state, user_response, level):
    # Обновляем промпт с упоминанием конкретного юзернейма для записи на урок
    summary_prompt = (
        "Ты - это я, Катя, репетитор польского языка. Пиши от моего имени личное сообщение ученику после проведенного теста. "
        f"Ученик показал уровень {level}. Вот его ответ на задание рассказать о себе на польском:\n\n"
        f"\"{user_response}\"\n\n"
        "Мой стиль общения: дружелюбный, с личными обращениями, использую эмодзи, общаюсь на 'ты', как с другом. "
        "Я всегда начинаю с приветствия 'Привет! Это Катя 👋' и обязательно заканчиваю фразой 'Твой репетитор, Катя 💫'. "
        "Пиши так, будто мы уже знакомы и я лично просмотрела ответ ученика.\n\n"
        "Структура сообщения:\n"
        "1. Приветствие и представление (Привет! Это Катя 👋)\n"
        f"2. Личная реакция на ответ ученика ('Я прочитала твой ответ и...')\n"
        f"3. Краткая оценка текущего уровня {level} (1 предложение)\n"
        "4. Одно конкретное достижение, что ученик делает правильно (с примером из его ответа)\n"
        "5. Одна главная ошибка, которую нужно исправить (с примером и простым объяснением)\n"
        "6. Раздел 'ДВА ПУТИ ОБУЧЕНИЯ:'\n"
        "   a) 'Вариант 1: Самостоятельное обучение' — план на 4 недели с конкретными микрозаданиями (по 2 на неделю)\n"
        "   b) 'Что ты достигнешь через месяц самостоятельных занятий' — 1 конкретный навык\n"
        "   c) 'Вариант 2: Занятия со мной' — краткое описание как проходят занятия (3-4 пункта)\n"
        "   d) 'Что ты достигнешь через месяц со мной' — 2-3 конкретных навыка (больше чем при самостоятельном обучении)\n"
        "7. 'Сравнение вариантов:'\n"
        "   a) 'Самостоятельно: плюсы' — 2 преимущества (например, гибкий график, бесплатно)\n"
        "   b) 'Самостоятельно: минусы' — 2 недостатка (например, нет обратной связи, медленнее прогресс)\n"
        "   c) 'Со мной: плюсы' — 3 преимущества (например, быстрый прогресс, разговорная практика, индивидуальный подход)\n"
        "   d) 'Со мной: минусы' — 1 недостаток (например, нужно подстраиваться под расписание)\n"
        "08. Подпись: 'Твой репетитор, Катя 💫'\n\n"
        "Задания должны быть максимально конкретными и практическими. Пиши очень лично, как будто это сообщение "
        "от меня одному конкретному ученику. Используй 2-3 эмодзи в тексте для эмоциональности. "
        "В сравнении вариантов ненавязчиво подчеркни преимущества занятий со мной, но сохраняй объективность."
    )
    
    try:
        plan = await get_grok_response(summary_prompt, TEST_SYSTEM_PROMPT)
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