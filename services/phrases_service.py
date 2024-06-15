import json
import random
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from assistant_api import AssistantsAPI
import config

# Load the assistant configuration
with open("assistant_config.json") as file:
    assistant_config = json.load(file)

assistant_id = assistant_config["id"]

# Initialize the AssistantsAPI client
assistants_api = AssistantsAPI(api_key=config.ASSISTANTS_API_KEY)

async def fetch_content(prompt):
    instructions = "You are an expert in the Polish language. Generate 10 brief conversational phrases in Polish."
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": prompt}
    ]
    response = await assistants_api.call_assistant(
        model=config.GPT_MODEL,
        messages=messages,
        max_tokens=config.MAX_TOKENS,
        temperature=config.TEMPERATURE,
    )
    return response["choices"][0]["message"]["content"].strip()

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
