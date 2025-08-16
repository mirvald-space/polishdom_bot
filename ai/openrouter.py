import aiohttp
import logging
from config import settings

async def get_ai_response(prompt: str, system_prompt: str = None) -> str:
    # Check if OPENROUTER_API_KEY is provided
    if not settings.OPENROUTER_API_KEY:
        logging.warning("OPENROUTER_API_KEY not provided. Using fallback responses.")
        
        # Provide fallback responses based on the system prompt
        if system_prompt == WORD_SYSTEM_PROMPT:
            return "słowo|слово|To jest słowo.|Это слово."
        elif system_prompt == TEST_SYSTEM_PROMPT:
            return "Ваш уровень: [A2]. Вы показали базовые знания польского языка."
        elif system_prompt == INTERVIEW_SYSTEM_PROMPT:
            return "Вы хорошо подготовлены к интервью. Продолжайте практиковаться."
        else:
            return "Функция недоступна без API ключа OpenRouter."
    
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
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "HTTP-Referer": "https://github.com/zerox9dev/polishdom_bot",  # Optional, for tracking
                    "X-Title": "PolishDom Bot"  # Optional, for tracking
                },
                json={
                    "model": "openai/gpt-oss-20b:free",  # Using Claude 3.5 Sonnet as default
                    "messages": messages,
                    "stream": False,
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logging.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return f"Ошибка API: {response.status} - {error_text}"
                
                data = await response.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"Error in get_ai_response: {str(e)}")
        return f"Ошибка при запросе к API: {str(e)}"

# Системные промпты для разных задач
INTERVIEW_SYSTEM_PROMPT = """You are a Polish language interview assistant for Karta Polaka (Polish Card) preparation.
Conduct mock interviews in Russian, helping users prepare for real Polish Card interviews.
Provide constructive feedback and suggestions for improvement.
Be encouraging and supportive while maintaining professionalism."""

TEST_SYSTEM_PROMPT = """You are a Polish language assessment expert. 
Evaluate the user's Polish language level based on their responses and provide detailed feedback in Russian.
Determine their level according to CEFR standards (A1, A2, B1, B2, C1, C2).
Provide specific recommendations for improvement and next steps in their language learning journey."""

WORD_SYSTEM_PROMPT = """You are a Polish language teacher. Generate a word in Polish based on the given topic. 
Always respond in the format: {polish_word}|{russian_translation}|{example_in_polish}|{example_translation_in_russian}
The word and example should be appropriate for the student's level. 
The translations MUST be in Russian.
The example should be a simple, practical sentence using the word in everyday life."""
