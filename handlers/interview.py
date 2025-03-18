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
from aiogram.types import Voice
from utils.audio import transcribe_audio
import os

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
        exact_msg = "Каждый раз я буду выбирать случайный набор вопросов (от 3 до 50), как это происходит на реальном собеседовании с консулом.\n\n"
        
    message_text = (
        f"🎯 *Тренажер на сдачу экзамена на Карту Поляка*\n\n"
        f"Я буду задавать вопросы, которые могут встретиться на интервью.\n\n"
        f"{exact_msg} "
        f"*Отвечайте на польском языке, и я помогу улучшить ваши ответы.*\n"
        f"Вы можете указать количество вопросов, например: /interview 3.\n"
        f"Также вы можете отвечать голосовыми сообщениями. 🎤"
    )
    
    await message.answer(
        escape_markdown(message_text),
        parse_mode="MarkdownV2",
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


@router.message(StateFilter(InterviewStates.waiting_answer), F.voice)
async def handle_voice_message(message: Message, state: FSMContext):
    file_id = message.voice.file_id
    file = await message.bot.get_file(file_id)
    file_path = f"/tmp/{file_id}.ogg"
    
    await message.bot.download_file(file.file_path, file_path)
    await message.answer("🔄 Транскрибирую аудио...")
    
    text = await transcribe_audio(file_path)
    os.remove(file_path)
    
    if not text:
        await message.answer("⚠️ Не удалось распознать аудио.")
        return
    
    await message.answer(f"✅ Распознано: {text}")
    await process_answer(message, state, text)


# Обработчик ответов на вопросы
async def process_answer(message: Message, state: FSMContext, answer_text: str):
    # Получаем данные из состояния
    data = await state.get_data()
    question_index = data.get("question_index", 0)
    questions = data.get("questions", [])
    answers = data.get("answers", [])
    interview_questions = data.get("interview_questions", [])
    
    # Сохраняем текущий вопрос и ответ
    current_question = interview_questions[question_index]
    questions.append(current_question)
    answers.append(answer_text)
    
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
        # Весь код из handle_answer для обработки завершения
        await message.answer(f"🔄 Интервью завершено! Вы ответили на {len(questions)} вопросов. Анализирую ваши ответы...")
        
        # Создаем итоговый анализ - весь код из handle_answer, который идет после этого сообщения
        # [Скопировать весь остальной код из handle_answer, начиная с summary_prompt]
                
        # Создаем итоговый анализ
        summary_prompt = (
            "Создай два кратких отзыва на диалог интервью на Карту Поляка:\n\n"
            "Диалог:\n" +
            "\n".join(f"Консул: {q}\nКандидат: {a}" for q, a in zip(questions, answers)) +
            "\n\n"
            "1. ОТЗЫВ КОНСУЛА (2-3 предложения):\n"
            "Формально сообщи результат: интервью пройдено или не пройдено, без объяснения причин.\n"
            "Например: «Уважаемый кандидат, ваше интервью пройдено. Вы продемонстрировали необходимый уровень знания польской культуры и языка».\n\n"
            
            "2. ОТЗЫВ ОТ МЕНЯ КАТИ (репетитора):\n"
            "Начни с 'Привет! Это Катя 👋'. Общайся на 'ты', дружелюбно, с 2-3 эмодзи.\n"
            "- Если по мнению консула интервью пройдено: поздравь и отметь 1-2 сильные стороны ответов, но упомяни, что стоит подготовиться к другим возможным темам (консул может спросить что угодно).\n"
            "- Если не пройдено: ободри и четко отметь 1-2 ключевые области для улучшения с примерами.\n"
            "В любом случае предложи помощь: «Я помогла многим ученикам успешно пройти интервью. Запишись на консультацию!»\n"
            "Заверши подписью: «Твой репетитор, Катя 💫»"
        )
        
        try:
            summary = await get_grok_response(summary_prompt, INTERVIEW_SYSTEM_PROMPT)
            if not summary:
                raise ValueError("Пустой ответ от API")
                
            escaped_summary = escape_markdown(summary)
            
            # Добавляем кнопку записи на урок
            from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
            
            lesson_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎓 Записаться на консультацию", url=f"https://t.me/katarzyna11")]
                ]
            )
            
            # Очищаем состояние
            await state.clear()
            
            # Отправляем результат
            await message.answer(
                f"🎯 Результат интервью:\n\n{escaped_summary}",
                parse_mode="MarkdownV2",
                reply_markup=ReplyKeyboardRemove()
            )
            
            await message.answer(
                "Запишись на консультацию, чтобы повысить шансы на получение Карты Поляка! 👇",
                reply_markup=lesson_keyboard
            )
            
            await message.answer(
                "Хочешь пройти ещё одно интервью? Используй команду /interview",
                reply_markup=ReplyKeyboardRemove()
            )
            
        except Exception as e:
            logging.error(f"Error analyzing interview results: {e}")
            await message.answer(
                "Произошла ошибка при анализе результатов. Пожалуйста, попробуйте позже.",
                reply_markup=ReplyKeyboardRemove()
            )
            await state.clear()


@router.message(StateFilter(InterviewStates.waiting_answer), ~F.text.startswith("/"), ~F.text.startswith("❌"))
async def handle_answer(message: Message, state: FSMContext):
    if not message.text or message.text.strip() == "":
        await message.answer("Пожалуйста, введите ответ на вопрос.")
        return
    
    await process_answer(message, state, message.text)

# Обработчик для команд во время интервью
@router.message(StateFilter(InterviewStates.waiting_answer), F.text.startswith("/"))
async def block_commands(message: Message):
    if message.text not in ["/cancel_interview", "/help"]:
        await message.answer(
            "⚠️ Вы сейчас проходите интервью. Команды недоступны.\n"
            "Завершите интервью или нажмите '❌ Отменить интервью'."
        )