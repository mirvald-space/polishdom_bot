import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from openai import AsyncOpenAI
import config

client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

async def fetch_content(prompt):
    messages = [
        {"role": "system", "content": "You are an expert in the Polish language."},
        {"role": "user", "content": prompt}
    ]
    completion = await client.chat.completions.create(
        model=config.GPT_MODEL,
        messages=messages,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE,
    )
    return completion.choices[0].message.content.strip()

async def send_phrases(bot: Bot):
    attempts = 0
    prompt = config.PROMPT_TEMPLATE_PHARASES + "\nСгенерируйте 10 кратких разговорных фраз."
    
    while attempts < config.MAX_ATTEMPTS:
        attempts += 1
        content = await fetch_content(prompt)
        phrases = content.split('\n')
        phrases = [line.strip() for line in phrases if line.strip()]
        print(f"Attempt {attempts}: {len(phrases)} phrases found")

        if len(phrases) >= 10:
            limited_phrases = '\n\n'.join(phrases[:10])
            header = "<b>🗣 Разговорные фразы на польском языке</b>\n\n"
            footer = "\n\nЗнали ли вы эти фразы? Поделитесь в комментариях👇\n\n@polishdom"
            message = header + limited_phrases + footer
            await bot.send_message(chat_id=config.CHANNEL_ID, text=message, parse_mode='HTML')
            return
        else:
            print(f"Ошибка: Сгенерировано меньше 10 фраз или лишний текст. Повторный запрос... (попытка {attempts})")

    print(f"Ошибка: Не удалось получить достаточное количество элементов после {config.MAX_ATTEMPTS} попыток.")

phrases_scheduler = AsyncIOScheduler()
