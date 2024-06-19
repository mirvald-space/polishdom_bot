import json
from aiogram import Bot
import asyncio
import os

# Файл для хранения ID отправленных вопросов
SENT_QUESTIONS_FILE = 'sent_questions.json'

# Функция для чтения отправленных вопросов
def read_sent_questions():
    if os.path.exists(SENT_QUESTIONS_FILE):
        with open(SENT_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Функция для записи отправленных вопросов
def write_sent_questions(sent_questions):
    with open(SENT_QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(sent_questions, f)

async def send_quiz(bot: Bot, channel_id: str, quiz_file='words/quiz.json'):
    # Чтение данных из файла quiz.json
    with open(quiz_file, 'r', encoding='utf-8') as f:
        quizzes = json.load(f)

    # Чтение отправленных вопросов
    sent_questions = read_sent_questions()

    # Отфильтруем уже отправленные вопросы
    new_quizzes = [quiz for quiz in quizzes if quiz['id'] not in sent_questions]

    # Ограничим количество вопросов до 3
    limited_quizzes = new_quizzes[:3]

    for quiz in limited_quizzes:
        question = quiz['question']
        options = quiz['options']
        correct_option_id = options.index(quiz['answer'])

        await bot.send_poll(
            chat_id=channel_id,
            question=question,
            options=options,
            type='quiz',
            correct_option_id=correct_option_id,
            is_anonymous=True  # Сделаем опрос анонимным
        )
        
        # Добавим ID вопроса в список отправленных
        sent_questions.append(quiz['id'])
        await asyncio.sleep(5)  # Задержка между отправками викторин

    # Запись обновленного списка отправленных вопросов
    write_sent_questions(sent_questions)
