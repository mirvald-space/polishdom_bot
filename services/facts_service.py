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

async def send_facts(bot: Bot):
    attempts = 0
    prompt = config.PROMPT_TEMPLATE + "\nСгенерируйте 5 кратких фактов о Польше с краткими объяснениями."
    
    while attempts < config.MAX_ATTEMPTS:
        attempts += 1
        content = await fetch_content(prompt)
        facts = content.split('\n')
        facts = [line.strip() for line in facts if line.strip()]
        print(f"Attempt {attempts}: {len(facts)} facts found")

        if len(facts) >= 5:
            limited_facts = '\n\n'.join(facts[:5])
            header = "<b>🇵🇱 5 кратких фактов о Польше</b>\n\n"
            footer = "\n\nЗнали ли вы об этих фактах? Поделитесь в комментариях👇\n\n@polishdom"
            message = header + limited_facts + footer
            await bot.send_message(chat_id=config.CHANNEL_ID, text=message, parse_mode='HTML')
            return
        else:
            print(f"Ошибка: Сгенерировано меньше 5 фактов или лишний текст. Повторный запрос... (попытка {attempts})")

    print(f"Ошибка: Не удалось получить достаточное количество элементов после {config.MAX_ATTEMPTS} попыток.")

facts_scheduler = AsyncIOScheduler()
