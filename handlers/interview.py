import os
import random

from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from services.db import mongo  # Import the mongo instance
from services.interview_service import evaluate_answers, questions


class InterviewStates(StatesGroup):
    WELCOME = State()
    ASK_QUESTION = State()
    WAIT_ANSWER = State()
    SHOW_REPORT = State()
    ASK_FEEDBACK = State()

async def interview_welcome(callback: CallbackQuery, state: FSMContext):
    random.shuffle(questions)
    selected_questions = questions[:10]  # Select up to 10 questions randomly
    await state.update_data(current_question=0, questions_and_answers=[], selected_questions=selected_questions)
    welcome_message = (
        "Добро пожаловать!\nВам предстоит ответить на 10 вопросов.\n\nКаждый раз при перезапуске вы получите новый набор из 10 вопросов.\n\n"
        "Важно: Вы можете использовать любой язык, но настоятельно рекомендуем польский. 🇵🇱"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 Начать собеседование", callback_data="start_interview")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_interview")]
    ])
    await callback.message.answer(welcome_message, reply_markup=keyboard)
    await state.set_state(InterviewStates.WELCOME)

async def start_interview(callback: CallbackQuery, state: FSMContext):
    await ask_next_question(callback.message, state)

async def ask_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data.get('current_question', 0)
    selected_questions = data.get('selected_questions', [])

    if current_question < len(selected_questions):
        question = selected_questions[current_question]
        await state.set_state(InterviewStates.WAIT_ANSWER)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data="cancel_interview")]
        ])
        await message.answer(question, reply_markup=keyboard)
    else:
        await message.answer("Вы ответили на все вопросы. Подождите немного, пока бот обработает ваши ответы и составит подробный отчет. Это займет всего несколько секунд. ⏳")
        await show_report(message, state)

async def handle_user_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data.get('current_question')
    questions_and_answers = data.get('questions_and_answers', [])
    selected_questions = data.get('selected_questions', [])

    if not selected_questions or current_question >= len(selected_questions):
        await message.answer("Ошибка в процессе собеседования. Пожалуйста, начните заново.")
        await state.clear()
        return

    question = selected_questions[current_question]
    user_answer = message.text

    # Update state
    questions_and_answers.append({"question": question, "answer": user_answer})
    await state.update_data(
        current_question=current_question + 1,
        questions_and_answers=questions_and_answers
    )

    await ask_next_question(message, state)

async def show_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    questions_and_answers = data.get('questions_and_answers', [])

    # Evaluate all answers
    evaluation = await evaluate_answers(questions_and_answers)
    
    # Extract scores and calculate average score
    scores = [int(line.split("Баллы: ")[1].split("/")[0]) for line in evaluation.split("\n\n") if "Баллы: " in line]
    total_score = sum(scores)
    average_score = total_score / len(scores) if scores else 0

    # Form full report
    report = f"""
<b>📄 Ваш отчет о собеседовании:</b>
<b>🏅 Общий балл:</b> {total_score} из {len(scores) * 10}
<b>📊 Средний балл:</b> {average_score:.2f}

<b>💡 Рекомендация:</b> {'Вы хорошо подготовлены к собеседованию.' if average_score >= 7 else 'Вам стоит лучше подготовиться к собеседованию.'}

<b>🔍 Подробная оценка ваших ответов:</b>
{evaluation}
    """

    # Split report into multiple messages if it exceeds Telegram's message length limit
    MAX_MESSAGE_LENGTH = 4096
    messages = [report[i:i + MAX_MESSAGE_LENGTH] for i in range(0, len(report), MAX_MESSAGE_LENGTH)]

    # Send each part of the report as a separate message
    for part in messages:
        await message.answer(part, parse_mode="HTML")

    await ask_feedback(message, state)

async def ask_feedback(message: types.Message, state: FSMContext):
    feedback_message = "Пожалуйста, оцените качество функции собеседования от 1 до 5:"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"feedback_{i}") for i in range(1, 6)]
    ])
    await message.answer(feedback_message, reply_markup=keyboard)
    await state.set_state(InterviewStates.ASK_FEEDBACK)

async def handle_feedback(callback: CallbackQuery, state: FSMContext):
    feedback_rating = int(callback.data.split('_')[1])
    user_id = callback.from_user.id
    username = callback.from_user.username

    # Save feedback to database using the mongo instance
    await mongo.save_interview_evaluation(user_id, username, feedback_rating)

    await callback.message.answer(f"Спасибо за вашу оценку: {feedback_rating}!")
    await return_to_main_menu(callback, state)

async def cancel_interview(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Собеседование было отменено. Вы вернулись в главное меню.")
    await return_to_main_menu(callback, state)

async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await callback.message.answer("Вы вернулись в главное меню. Выберите нужный раздел:", reply_markup=keyboard)
    await callback.answer()
    await state.clear()

async def register_interview_handlers(dp: Dispatcher):
    dp.callback_query.register(interview_welcome, lambda c: c.data == "interview")
    dp.callback_query.register(start_interview, lambda c: c.data == "start_interview")
    dp.message.register(handle_user_answer, InterviewStates.WAIT_ANSWER)
    dp.callback_query.register(cancel_interview, lambda c: c.data == "cancel_interview")
    dp.callback_query.register(return_to_main_menu, lambda c: c.data == "main_menu")
    dp.callback_query.register(handle_feedback, lambda c: c.data.startswith("feedback_"))
