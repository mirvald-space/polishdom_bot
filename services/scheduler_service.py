import os
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_TEMPLATE = """
You are an expert in the Polish language and in films. Your task is to generate content for a Polish learning channel. The content must strictly follow the specified format and include exactly the required number of items with no additional text or explanation. Do not include any headings or explanations. Ensure there are no empty lines or additional text between items.

1. Generate a selection of movies for levels A1-B2. There should be exactly 5 movies in the following format:
Title (Year) ⭐ Rating
Example:
Incepcja (2010) ⭐ 8.8
Your response should be:
Title (Year) ⭐ Rating
Title (Year) ⭐ Rating
Title (Year) ⭐ Rating
Title (Year) ⭐ Rating
Title (Year) ⭐ Rating

2. Generate conversational phrases in Polish with Russian translation. There should be exactly 10 phrases in the following format:
Polish phrase — Translation in Russian
Example:
Jak się masz? — Как дела?
Your response should be:
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian
Polish phrase — Translation in Russian

Ensure that there are exactly 5 movies or 10 phrases, and nothing more. Do not include any headings or explanations. Ensure there are no empty lines or additional text between items.
"""

def escape_markdown(text):
    escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    return ''.join(['\\' + char if char in escape_chars else char for char in text])

async def fetch_content(prompt):
    messages = [
        {"role": "system", "content": "You are an expert in the Polish language and in films."},
        {"role": "user", "content": prompt}
    ]
    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        temperature=0.7,
    )
    return completion.choices[0].message.content.strip()

async def send_scheduled_message(bot: Bot, content_type: str):
    max_attempts = 5  # Максимальное количество попыток
    attempts = 0

    if content_type == "movies":
        prompt = PROMPT_TEMPLATE + "\nGenerate a selection of movies for level A1-B2. There should be exactly 5 movies in the specified format."
        while attempts < max_attempts:
            attempts += 1
            content = await fetch_content(prompt)
            movies = content.split('\n')
            movies = [line.strip() for line in movies if line.strip()]
            if len(movies) == 5 and all('⭐' in movie for movie in movies):
                limited_movies = '\n'.join(movies)
                header = "🎬 Подборка фильмов для уровней A1-B2\n\n"
                message = escape_markdown(header + limited_movies)
                await bot.send_message(chat_id=os.getenv("CHANNEL_ID"), text=message, parse_mode='MarkdownV2')
                return
            else:
                print(f"Ошибка: Сгенерировано меньше 5 фильмов или лишний текст. Повторный запрос... (попытка {attempts})")
    elif content_type == "phrases":
        prompt = PROMPT_TEMPLATE + "\nGenerate a selection of conversational phrases. There should be exactly 10 phrases in the specified format."
        while attempts < max_attempts:
            attempts += 1
            content = await fetch_content(prompt)
            phrases = content.split('\n')
            phrases = [line.strip() for line in phrases if line.strip()]
            if len(phrases) == 10 and all('—' in phrase for phrase in phrases):
                limited_phrases = '\n'.join(phrases)
                header = "🗣 Разговорные фразы на польском языке\n\n"
                message = escape_markdown(header + limited_phrases)
                await bot.send_message(chat_id=os.getenv("CHANNEL_ID"), text=message, parse_mode='MarkdownV2')
                return
            else:
                print(f"Ошибка: Сгенерировано меньше 10 фраз или лишний текст. Повторный запрос... (попытка {attempts})")

    print(f"Ошибка: Не удалось получить достаточное количество элементов после {max_attempts} попыток.")

scheduler = AsyncIOScheduler()
