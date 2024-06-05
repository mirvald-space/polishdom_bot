from aiogram import Dispatcher, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from services.openai_service import client, questions, evaluate_answers
import os
import tempfile
from pydub import AudioSegment
import speech_recognition as sr

class InterviewStates(StatesGroup):
    WELCOME = State()
    ASK_QUESTION = State()
    WAIT_ANSWER = State()
    SHOW_REPORT = State()

async def interview_welcome(callback: CallbackQuery, state: FSMContext):
    await state.update_data(current_question=0, questions_and_answers=[])
    welcome_message = (
        "Вы будете отвечать на 15 вопросов. Пожалуйста, отвечайте на вопросы на польском языке, так как собеседование будет проводиться на этом языке.\n\n"
        "Важно: вы можете отвечать на вопросы как письменно, так и голосом. Главное, отвечать на польском. Если вы отвечаете голосом, постарайтесь говорить четко и разборчиво, чтобы ваш ответ мог быть нормально оценен."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Начать собеседование", callback_data="start_interview")]
    ])
    await callback.message.answer(welcome_message, reply_markup=keyboard)
    await state.set_state(InterviewStates.WELCOME)

async def start_interview(callback: CallbackQuery, state: FSMContext):
    await ask_next_question(callback.message, state)

async def ask_next_question(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data['current_question']
    if current_question < len(questions):
        question = questions[current_question]
        await state.set_state(InterviewStates.WAIT_ANSWER)
        await message.answer(question)
    else:
        await show_report(message, state)

async def handle_user_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    current_question = data['current_question']
    questions_and_answers = data['questions_and_answers']
    question = questions[current_question]

    if message.voice:
        # Get voice message
        file_id = message.voice.file_id
        file = await message.bot.get_file(file_id)
        file_path = file.file_path

        # Download voice message
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_file:
            await message.bot.download_file(file_path, temp_file.name)
            audio_path = temp_file.name

        try:
            # Convert OGG to WAV using pydub
            audio = AudioSegment.from_file(audio_path, format="ogg")
            wav_path = audio_path.replace(".ogg", ".wav")
            audio.export(wav_path, format="wav")

            # Use speech_recognition to transcribe the WAV file
            recognizer = sr.Recognizer()
            with sr.AudioFile(wav_path) as source:
                audio_data = recognizer.record(source)  # Read the entire audio file
                user_answer = recognizer.recognize_google(audio_data, language="pl-PL")

        except Exception as e:
            print(f"Error: {e}")
            await message.answer("Произошла ошибка при обработке голосового сообщения. Попробуйте снова или используйте текстовый ответ.")
            return
    else:
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
    questions_and_answers = data['questions_and_answers']

    # Evaluate all answers
    evaluation = await evaluate_answers(questions_and_answers)
    
    # Extract scores and calculate average score
    scores = [int(line.split("Баллы: ")[1].split("/")[0]) for line in evaluation.split("\n") if "Баллы: " in line]
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
