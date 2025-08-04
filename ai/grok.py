import aiohttp
import logging
from config import settings

async def get_grok_response(prompt: str, system_prompt: str = None) -> str:
    # Check if GROK_API_KEY is provided
    if not settings.GROK_API_KEY:
        logging.warning("GROK_API_KEY not provided. Using fallback responses.")
        
        # Provide fallback responses based on the system prompt
        if system_prompt == WORD_SYSTEM_PROMPT:
            return "słowo|слово|To jest słowo.|Это слово."
        elif system_prompt == TEST_SYSTEM_PROMPT:
            return "Ваш уровень: [A2]. Вы показали базовые знания польского языка."
        elif system_prompt == INTERVIEW_SYSTEM_PROMPT:
            return "Вы хорошо подготовлены к интервью. Продолжайте практиковаться."
        else:
            return "Функция недоступна без API ключа Grok."
    
    try:
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.x.ai/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.GROK_API_KEY}"
                },
                json={
                    "messages": messages,
                    "model": "grok-4-latest",
                    "stream": False,
                    "temperature": 0
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"Grok API error: {response.status} - {error_text}")
                    return f"Ошибка API: {response.status} - {error_text}"
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error in get_grok_response: {str(e)}")
        return f"Ошибка при запросе к API: {str(e)}"

# Системные промпты для разных задач
INTERVIEW_SYSTEM_PROMPT = "You are a Polish language interview assistant."
TEST_SYSTEM_PROMPT = "You are a Polish language assessment expert. Evaluate the language level and provide detailed feedback."
WORD_SYSTEM_PROMPT = """You are a Polish language teacher. Generate a word in Polish based on the given topic. 
Always respond in the format: {polish_word}|{russian_translation}|{example_in_polish}|{example_translation_in_russian}
The word and example should be appropriate for the student's level. 
The translations MUST be in Russian.
The example should be a simple, practical sentence using the word in everyday life.""" 
