import os
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_TEMPLATE = """
Every week I want to publish content in Polish for the channel. The content should include:

Conversational phrases in Polish with Russian translation. Example (exactly 10 phrases per post):
Cześć — Привет
Jak się masz? — Как дела?
"""

async def fetch_content(prompt):
    messages = [
        {"role": "system", "content": "You are an expert in the Polish language."},
        {"role": "user", "content": prompt}
    ]
    completion = await client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=1500,
        temperature=0.7,
    )
    return completion.choices[0].message.content.strip()

async def send_phrases(bot: Bot):
    max_attempts = 5  # Максимальное количество попыток
    attempts = 0
    prompt = PROMPT_TEMPLATE + "\nGenerate a selection of conversational phrases. There should be exactly 10 phrases in the specified format."
    
    while attempts < max_attempts:
        attempts += 1
        content = await fetch_content(prompt)
        phrases = content.split('\n')
        phrases = [line.strip() for line in phrases if '—' in line]
        print(f"Attempt {attempts}: {len(phrases)} phrases found")

        if len(phrases) == 10:
            limited_phrases = '\n'.join(phrases)
            header = "<b>🗣 Разговорные фразы на польском языке</b>\n\n"
            message = header + limited_phrases
            await bot.send_message(chat_id=os.getenv("CHANNEL_ID"), text=message, parse_mode='HTML')
            return
        else:
            print(f"Ошибка: Сгенерировано меньше 10 фраз или лишний текст. Повторный запрос... (попытка {attempts})")

    print(f"Ошибка: Не удалось получить достаточное количество элементов после {max_attempts} попыток.")

phrases_scheduler = AsyncIOScheduler()
