import re
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import logging
from ai.grok import get_grok_response, TEST_SYSTEM_PROMPT
from datetime import datetime
from utils.markdown import escape_markdown

router = Router()
router.message.filter(F.chat.type == "private")

# Состояния теста
class TestStates(StatesGroup):
    waiting_answer = State()      # Ожидание ответа на вопрос

# Вопросы для теста
TEST_QUESTIONS = [
    "Opowiedz mi o sobie po polsku.",
    "Co lubisz robić w wolnym czasie?",
    "Jakie masz plany na przyszłość?",
    "Dlaczego uczysz się języka polskiego?",
    "Opowiedz o swoim mieście.",
    "Jakie masz ulubione polskie potrawy?"
]

# Клавиатура для управления тестом
def get_test_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить тест")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Клавиатура для старта теста
def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Начать тест")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Команда для начала теста
@router.message(Command("test"))
async def cmd_test(message: Message, state: FSMContext):
    # Проверяем текущее состояние
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_test_keyboard()
        )
        return
        
    await message.answer(
        "📝 Тест уровня польского языка\n\n"
        "Я задам вам несколько вопросов, чтобы определить ваш уровень владения языком. "
        "Отвечайте на польском языке максимально полно.",
        reply_markup=get_start_keyboard()
    )

# Обработчик нажатия кнопки или ввода команды для начала теста
@router.message(F.text == "📝 Начать тест")
@router.message(Command("start_test"))
async def start_test(message: Message, state: FSMContext):
    # Проверяем, нет ли уже активного состояния
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_test_keyboard()
        )
        return
    
    # Инициализируем данные для теста
    await state.set_state(TestStates.waiting_answer)
    await state.update_data(
        question_index=0,
        questions=[],
        answers=[],
        start_time=datetime.utcnow()
    )
    
    # Отправляем первый вопрос
    await message.answer(
        TEST_QUESTIONS[0],
        reply_markup=get_test_keyboard()
    )

# Обработчик отмены теста
@router.message(F.text == "❌ Отменить тест")
@router.message(Command("cancel_test"))
async def cancel_test(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        # Очищаем состояние
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

# Обработчик ответов на вопросы
@router.message(StateFilter(TestStates.waiting_answer), ~F.text.startswith("/"), ~F.text.startswith("❌"))
async def handle_answer(message: Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    questions = data.get("questions", [])
    answers = data.get("answers", [])
    
    # Проверка на пустой ответ
    if not message.text or message.text.strip() == "":
        await message.answer("Пожалуйста, введите ответ на вопрос.")
        return
    
    # Сохраняем текущий вопрос и ответ
    current_question = TEST_QUESTIONS[question_index]
    questions.append(current_question)
    answers.append(message.text)
    
    # Переходим к следующему вопросу или завершаем
    next_index = question_index + 1
    
    if next_index < len(TEST_QUESTIONS):
        # Сохраняем обновленные данные
        await state.update_data(
            question_index=next_index,
            questions=questions,
            answers=answers
        )
        
        # Отправляем следующий вопрос
        await message.answer(TEST_QUESTIONS[next_index])
    else:
        # Все вопросы заданы, создаем анализ
        await message.answer("🔄 Анализирую ваши ответы и определяю уровень польского языка...")
        
        # Создаем итоговый анализ
        # Промпт для анализа теста от имени репетитора
        summary_prompt = (
            "Ты - репетитор польского языка. Проанализируй ответы ученика и дай краткую обратную связь (не более 8-10 предложений). Определи уровень владения польским (A1-C2), отметь сильные стороны и главные ошибки. Обращайся к ученику на 'вы'.\n\n"
            "Ответы ученика:\n" +
            "\n".join(f"Вопрос: {q}\nОтвет: {a}" for q, a in zip(questions, answers)) +
            "\n\n"
            "Структура ответа:\n"
            "📊 *Ваш уровень: [УРОВЕНЬ]* (укажи один из: A1, A2, B1, B2, C1, C2)\n\n"
            "✅ *Что получается хорошо:* (1-2 конкретных момента с примерами из ответов)\n\n"
            "🔍 *Над чем поработать:* (1-2 основные ошибки с кратким объяснением)\n\n"
            "📚 *Совет от репетитора:* (1 практическое упражнение или ресурс)\n\n"
            "Используй поддерживающий, но честный тон. Цитируй примеры из ответов ученика."
        )
        
        try:
            summary = await get_grok_response(summary_prompt, TEST_SYSTEM_PROMPT)
            if not summary:
                raise ValueError("Пустой ответ от API")
                
                
            escaped_summary = escape_markdown(summary)
            
            # Извлекаем уровень из анализа
            level_match = re.search(r"\*Ваш уровень: \[(A[12]|B[12]|C[12])\]\*", summary)
            if not level_match:
                # Пробуем альтернативные форматы
                level_match = re.search(r"Ваш уровень:?\s*\[?(A[12]|B[12]|C[12])\]?", summary)
            level = level_match.group(1) if level_match else "A2"
            
            # Сохраняем уровень пользователя
            # Переносим import за пределы функции для избежания циклического импорта
            try:
                from db.mongo import db
                await db.update_user_level(message.from_user.id, level)
                logging.info(f"Updated user {message.from_user.id} language level to {level}")
            except Exception as e:
                logging.error(f"Failed to update user level: {e}")
            
            # Очищаем состояние
            await state.clear()
            
            # Отправляем результат
            await message.answer(
                f"📝 Результаты теста польского языка:\n\n{escaped_summary}",
                parse_mode="MarkdownV2",
                reply_markup=ReplyKeyboardRemove()
            )
            
            await message.answer(
                "Вы можете пройти тест снова командой /test или начать практику с /help",
                reply_markup=ReplyKeyboardRemove()
            )
            
        except Exception as e:
            logging.error(f"Error analyzing test results: {e}")
            await message.answer(
                "Произошла ошибка при анализе результатов. Пожалуйста, попробуйте позже.",
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