import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME')
MONGO_COLLECTION_NAME = os.getenv('MONGO_COLLECTION_NAME')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TMDB_API_KEY = os.getenv('TMDB_API_KEY')
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Prompt templates
PROMPT_TEMPLATE = """
Every week I want to publish content on the topic of Polish language, the content should include >=5 short facts about Poland with a brief explanation, very critically without unnecessary headlines, exclusively facts, in Polish, also facts should not be related to each other, each fact should be new and interesting. Example:
1️⃣ Polska graniczy z siedmioma krajami: Niemcami, Czechami, Słowacją, Ukrainą, Białorusią, Litwą i Rosją.

2️⃣ W Polsce znajduje się największa pustynia w Europie – Pustynia Błędowska, która ma powierzchnię około 33 km².

3️⃣ Wrocław, jedno z największych miast w Polsce, jest znane z licznych mostów i kładek – jest ich tam ponad 120.

4️⃣ Polska jest jednym z największych producentów bursztynu na świecie; większość bursztynu pochodzi z wybrzeża Morza Bałtyckiego.

5️⃣ W Polsce znajduje się Puszcza Białowieska, jeden z ostatnich i największych pierwotnych lasów nizinnych w Europie.

"""

PROMPT_TEMPLATE_PHARASES="""
Every week I want to publish content on the topic of Polish language, the content should include >=10 short popular conversational phrases in Polish-Russian translation, very critically, without unnecessary headings, exclusively phrases, in Polish and translation in Russian, also phrases should not be related to each other, each phrase should be new and interesting. Example:
1. Dzień dobry — Добрый день
2. Proszę — Пожалуйста
3. Dziękuję — Спасибо
4. Przepraszam — Извините
5. Jak się nazywasz? — Как тебя зовут?
6. Skąd jesteś? — Откуда ты?
7. Ile to kosztuje? — Сколько это стоит?
8. Gdzie jest toaleta? — Где находится туалет?
9. Czy mówisz po angielsku? — Ты говоришь по-английски?
10. Do widzenia — До свидания

"""


INTERVIEW_CONTEXT = """
You are an expert in the process of obtaining the "Karta Polaka" (Card of the Pole). 
Answer questions only related to the "Karta Polaka" and provide clear, structured, and concise information. 
If the question is unrelated, respond with "This question is not related to the Karta Polaka process."
Keep your answers within 1024 characters, ensuring the answers are clear and nothing important is left out.
"""

EVALUATION_CONTEXT = """
You are a Polish consul evaluating answers for the Karta Polaka interview.
The user's answers are provided below.
Provide feedback and a score out of 10 for each answer.
Translate the feedback into Russian.
Format your response as follows:
Вопрос: <question>
Ответ: <answer>
Оценка: <feedback>. Баллы: <score>/10.
"""

# Scheduler configuration
MAX_ATTEMPTS = 5
GPT_MODEL = "gpt-4o"
MAX_TOKENS = 1500
TEMPERATURE = 0.7
MAX_CHARACTERS = 1024

# Interview questions
INTERVIEW_QUESTIONS = [
    "Dlaczego Pani/Panu jest potrzebna Karta Polaka?",
    "Proszę opowiedzieć о swojej rodzinie i polskich korzeniach?",
    "Jakie tradycje obchodzą Państwo na Boże Narodzenie?",
    "Kto jest autorem książki 'Pan Tadeusz'?",
    "Jakie polskie święta Pani/Pan zna? Jak je Pani/Pan obchodzi?",
    "Co znaczy pojęcie „Narodowość” dla Pani? Proszę uzasadnić swoją wypowiedź.",
    "Co Pani/Pan zna o historii Polski?",
    "Proszę nazwać pełną datę bitwy pod Grunwaldem?",
    "W którym roku stolica została przeniesiona z Krakowa do Warszawy? Kto był królem podczas tego wydarzenia?",
    "Proszę wymienić polskich noblistów oraz powiedzieć dlaczego i w jakiej dziedzinie otrzymali Nagrodę Nobla?",
    "Jakie polskie dania tradycyjne Pani/Pan zna? Proszę opisać przepis zupy „Żurek”.",
    "Jak długo i gdzie uczył(a) się Pan/Pani języka polskiego?",
    "Jakie zna Pani/Pan polskie filmy i książki? Proszę opowiedzieć o filmie „Katyń”.",
    "Czy ma Pani/Pan przyjaciół czy znajomych w Polsce?",
    "Jakie miasta czy miejsca Pani/Pan już zwiedzał(a)? Czy planuje zwiedzić w przyszłości?",
    "Kto napisał utwór „Ogniem i mieczem”?"
]

# TMDB API Configuration
TMDB_API_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# List of emojis to use for the header
EMOJIS = ["🎬", "🍿", "🎥", "📽️", "🎞️", "📺", "🎭"]

# Time settings for schedulers
PHRASES_SCHEDULE = {
    "day_of_week": "mon,thu",
    "hour": 9,
    "minute": 59
}

FACTS_SCHEDULE = {
    "day_of_week": "wed",
    "hour": 20,
    "minute": 5
}

MOVIES_SCHEDULE = {
    "day_of_week": "fri",
    "hour": 17,
    "minute": 50
}
