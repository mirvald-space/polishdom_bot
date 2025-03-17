from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from QUESTIONS.INTERVIEW_QUESTIONS import INTERVIEW_QUESTIONS
from ai.grok import get_grok_response, INTERVIEW_SYSTEM_PROMPT
from datetime import datetime
import logging
import random
from states.interview import InterviewStates
from utils.markdown import escape_markdown

router = Router()
router.message.filter(F.chat.type == "private")

# Функция для получения случайных вопросов
def get_random_questions(max_count=50):
    # Копируем список вопросов, чтобы не изменять оригинал
    all_questions = INTERVIEW_QUESTIONS.copy()
    # Перемешиваем вопросы
    random.shuffle(all_questions)
    
    # Если передано точное количество вопросов, используем его
    if isinstance(max_count, int) and max_count > 0 and max_count <= len(all_questions):
        return all_questions[:max_count]
    
    # Иначе определяем случайное количество вопросов
    min_questions = 3
    max_questions = min(50 if max_count is None else max_count, len(all_questions))
    
    # Проверяем, что min_questions < max_questions, чтобы избежать ошибки randint
    if min_questions >= max_questions:
        question_count = min_questions
    else:
        question_count = random.randint(min_questions, max_questions)
    
    # Возвращаем нужное количество вопросов
    return all_questions[:question_count]

# Клавиатура для управления интервью
def get_interview_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❌ Отменить интервью")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard

# Клавиатура для старта интервью
def get_start_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Начать интервью")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard

# Команда для начала интервью
@router.message(Command("interview"))
async def cmd_interview(message: Message, state: FSMContext):
    # Проверяем текущее состояние
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_interview_keyboard()
        )
        return
    
    # Проверяем, есть ли аргумент для количества вопросов
    cmd_args = message.text.split()
    exact_questions = None
    
    # Пытаемся получить число вопросов из аргумента, если он есть
    if len(cmd_args) > 1:
        try:
            num_questions = int(cmd_args[1])
            if 1 <= num_questions <= 50:  # Ограничиваем диапазон от 1 до 50
                exact_questions = num_questions
            else:
                await message.answer(
                    "⚠️ Количество вопросов должно быть от 1 до 50. Будет выбрано случайное количество."
                )
        except ValueError:
            pass
    
    # Сохраняем точное количество вопросов, если задано
    if exact_questions:
        await state.update_data(exact_questions=exact_questions)
        exact_msg = f"Вам будет задано ровно {exact_questions} вопросов."
    else:
        exact_msg = "Каждый раз я буду выбирать случайный набор вопросов (от 3 до 50), как это происходит на реальном собеседовании с консулом."
        
    await message.answer(
        f"🎯 Подготовка к Карте Поляка\n\n"
        f"Я буду задавать вопросы, которые могут встретиться на интервью. "
        f"{exact_msg} "
        f"Отвечайте на польском языке, и я помогу улучшить ваши ответы.",
        reply_markup=get_start_keyboard()
    )

# Обработчик нажатия кнопки или ввода команды для начала интервью
@router.message(F.text == "🎯 Начать интервью")
@router.message(Command("start_interview"))
async def start_interview(message: Message, state: FSMContext):
    # Проверяем, нет ли уже активного состояния
    current_state = await state.get_state()
    if current_state:
        await message.answer(
            "У вас уже есть активный процесс. Завершите его или отмените текущий.",
            reply_markup=get_interview_keyboard()
        )
        return
    
    # Получаем данные из состояния, если они есть
    data = await state.get_data()
    exact_questions = data.get("exact_questions", None)
    
    # Получаем набор вопросов
    random_questions = get_random_questions(exact_questions)
    
    # Инициализируем данные для интервью
    await state.set_state(InterviewStates.waiting_answer)
    await state.update_data(
        question_index=0,
        questions=[],
        answers=[],
        interview_questions=random_questions,  # Сохраняем выбранные вопросы
        start_time=datetime.utcnow()
    )
    
    await message.answer(
        f"Начинаем интервью! Вам будет задано {len(random_questions)} вопросов.",
        reply_markup=get_interview_keyboard()
    )
    
    # Отправляем первый вопрос
    await message.answer(
        random_questions[0],
        reply_markup=get_interview_keyboard()
    )

# Обработчик отмены интервью
@router.message(F.text == "❌ Отменить интервью")
@router.message(Command("cancel_interview"))
async def cancel_interview(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state:
        # Очищаем состояние и все данные
        await state.clear()
        await message.answer(
            "✅ Интервью отменено.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            "У вас нет активного интервью.",
            reply_markup=ReplyKeyboardRemove()
        )

# Обработчик ответов на вопросы
@router.message(StateFilter(InterviewStates.waiting_answer), ~F.text.startswith("/"), ~F.text.startswith("❌"))
async def handle_answer(message: Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    questions = data.get("questions", [])
    answers = data.get("answers", [])
    interview_questions = data.get("interview_questions", [])
    
    # Проверка на пустой ответ
    if not message.text or message.text.strip() == "":
        await message.answer("Пожалуйста, введите ответ на вопрос.")
        return
    
    # Сохраняем текущий вопрос и ответ
    current_question = interview_questions[question_index]
    questions.append(current_question)
    answers.append(message.text)
    
    # Переходим к следующему вопросу или завершаем
    next_index = question_index + 1
    
    if next_index < len(interview_questions):
        # Сохраняем обновленные данные
        await state.update_data(
            question_index=next_index,
            questions=questions,
            answers=answers
        )
        
        # Отправляем следующий вопрос
        await message.answer(interview_questions[next_index])
    else:
        # Все вопросы заданы, создаем анализ
        await message.answer(f"🔄 Интервью завершено! Вы ответили на {len(questions)} вопросов. Анализирую ваши ответы...")
        
        # Создаем итоговый анализ
        summary_prompt = (
            "На основе этого диалога, дай два коротких отзыва - от консула и от репетитора. Обращайся к кандидату напрямую, на 'вы'.\n\n"
            "Диалог:\n" +
            "\n".join(f"Консул: {q}\nКандидат: {a}" for q, a in zip(questions, answers)) +
            "\n\n💼 *Консул:*\n"
            "\"Уважаемый кандидат, я оценил(а) ваше интервью. "
            "Ваши сильные стороны - это [...]. "
            "Однако обратите внимание на [...]. "
            "Рекомендую вам подготовить более развернутые ответы о [...]. "
            "В целом, ваша готовность к получению Карты Поляка [...].\"\n\n"
            "👨‍🏫 *Репетитор польского языка:*\n"
            "\"Здравствуйте! Я проанализировал(а) ваш польский язык. "
            "Ваш уровень языка примерно [УРОВЕНЬ] (укажи один из: A1, A2, B1, B2, C1, C2). "
            "Вы хорошо справляетесь с [...], "
            "но нужно поработать над [...]. "
            "Давайте сосредоточимся на этих аспектах грамматики: [...]. "
            "Рекомендую следующие упражнения: [...].\"\n\n"
            "Заполни [...] конкретными наблюдениями из ответов кандидата. В месте [УРОВЕНЬ] обязательно укажи только один из перечисленных уровней. Сохраняй прямое обращение и разговорный тон."
        )
        
        try:
            summary = await get_grok_response(summary_prompt, INTERVIEW_SYSTEM_PROMPT)
            if not summary:
                raise ValueError("Пустой ответ от API")
                
            escaped_summary = escape_markdown(summary)
            
            # Очищаем состояние
            await state.clear()
            
            # Отправляем результат
            await message.answer(
                f"🎯 Анализ вашей подготовки к Карте Поляка:\n\n{escaped_summary}",
                parse_mode="MarkdownV2",
                reply_markup=ReplyKeyboardRemove()
            )
            
            await message.answer(
                "Вы можете начать новое интервью командой /interview. Каждый раз вопросы будут выбираться случайным образом.",
                reply_markup=ReplyKeyboardRemove()
            )
            
        except Exception as e:
            logging.error(f"Error analyzing interview results: {e}")
            await message.answer(
                "Произошла ошибка при анализе результатов. Пожалуйста, попробуйте позже.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()

# Обработчик для команд во время интервью
@router.message(StateFilter(InterviewStates.waiting_answer), F.text.startswith("/"))
async def block_commands(message: Message):
    if message.text not in ["/cancel_interview", "/help"]:
        await message.answer(
            "⚠️ Вы сейчас проходите интервью. Команды недоступны.\n"
            "Завершите интервью или нажмите '❌ Отменить интервью'."
        )