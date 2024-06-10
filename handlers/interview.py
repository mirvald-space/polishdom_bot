from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.interview_service import client, questions, evaluate_answers
import random

class InterviewStates(StatesGroup):
    WELCOME = State()
    ASK_QUESTION = State()
    WAIT_ANSWER = State()
    SHOW_REPORT = State()

async def interview_welcome(callback: CallbackQuery, state: FSMContext):
    random.shuffle(questions)
    selected_questions = questions[:10]  # Select up to 10 questions randomly
    await state.update_data(current_question=0, questions_and_answers=[], selected_questions=selected_questions)
    welcome_message = (
        "Вы будете отвечать на 10 вопросов. Пожалуйста, отвечайте на вопросы на польском языке, так как собеседование будет проводиться на этом языке.\n\n"
        "Важно: вы можете отвечать на вопросы любом языке. Рекомендуем, отвечать на польском.🇵🇱"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏁 Начать собеседование", callback_data="start_interview")]
    ])
    await callback.message.answer(welcome_message, reply_markup=keyboard)
    await state.set_state(InterviewStates.WELCOME)

async def start_interview(callback: CallbackQuery, state: FSMContext):
    await ask_next_question(callback.message, state)

async def ask_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data.get('current_question', 0)  # Default to 0 if key is missing
    selected_questions = data.get('selected_questions', [])

    if current_question < len(selected_questions):
        question = selected_questions[current_question]
        await state.set_state(InterviewStates.WAIT_ANSWER)
        await message.answer(question)
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

    # Button to return to main menu
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Вернуться в главное меню", callback_data="main_menu")]
    ])
    await message.answer("Отчет завершен. Вернуться в главное меню:", reply_markup=keyboard)
    await state.clear()

async def return_to_main_menu(callback: CallbackQuery, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Проверка уровня языка", callback_data="test")],
        [InlineKeyboardButton(text="Подготовка к собеседованию", callback_data="interview")]
    ])
    await callback.message.answer("Вы вернулись в главное меню. Выберите нужный раздел:", reply_markup=keyboard)
    await callback.answer()
    await state.clear()

def register_interview_handlers(dp: Dispatcher):
    dp.callback_query.register(interview_welcome, lambda c: c.data == "interview")
    dp.callback_query.register(start_interview, lambda c: c.data == "start_interview")
    dp.message.register(handle_user_answer, InterviewStates.WAIT_ANSWER)
    dp.callback_query.register(return_to_main_menu, lambda c: c.data == "main_menu")
