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

WEBHOOK_URL = os.getenv('WEBHOOK_URL')
WEBHOOK_PATH = '/bot_webhook'
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = 8000



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
    "Kto napisał utwór „Ogniem i mieczem”?",
    "Proszę opowiedzieć o polskich symbolach narodowych.",
    "Proszę wymienić polskich kompozytorów i ich dzieła.",
    "Kiedy odbyła się bitwa warszawska?",
    "Kim był Jan Paweł II?",
    "Proszę wymienić polskich prezydentów od roku 1989.",
    "Jakie są najważniejsze rzeki w Polsce?",
    "Proszę wymienić polskich poetów i ich wiersze.",
    "Jakie polskie góry Pani/Pan zna? Proszę opisać jedną z nich.",
    "Co Pani/Pan wie o Konstytucji 3 maja?",
    "Kim był Józef Piłsudski?",
    "Proszę opisać Polską Akademię Nauk.",
    "Jakie są główne regiony Polski?",
    "Proszę wymienić polskie zespoły muzyczne i ich popularne utwory.",
    "Proszę wymienić polskich reżyserów filmowych i ich filmy.",
    "Jakie są najważniejsze zabytki Krakowa?",
    "Co Pani/Pan wie o historii Uniwersytetu Jagiellońskiego?",
    "Jakie są najważniejsze miasta w Polsce?",
    "Proszę opowiedzieć o polskich tradycjach wielkanocnych.",
    "Kim była Maria Skłodowska-Curie?",
    "Proszę wymienić najważniejsze wydarzenia z historii Polski w XX wieku.",
    "Jakie są najważniejsze zabytki Warszawy?",
    "Proszę opowiedzieć o polskiej kuchni.",
    "Kim był Fryderyk Chopin?",
    "Proszę opowiedzieć o historii Gdańska.",
    "Jakie są główne atrakcje turystyczne w Polsce?",
    "Kim był Lech Wałęsa?",
    "Proszę wymienić polskich sportowców i ich osiągnięcia.",
    "Jakie są główne porty morskie w Polsce?",
    "Proszę opowiedzieć o polskich tradycjach i obyczajach.",
    "Jakie są najważniejsze jeziora w Polsce?",
    "Proszę wymienić polskich malarzy i ich dzieła.",
    "Jakie są główne produkty eksportowe Polski?",
    "Proszę opowiedzieć o polskich legendach i baśniach.",
    "Jakie są najważniejsze wydarzenia kulturalne w Polsce?",
    "Proszę opowiedzieć o polskich zamkach i pałacach.",
    "Jakie są najważniejsze regiony w Polsce pod względem turystycznym?",
    "Proszę opowiedzieć o polskich tradycjach związanych z Nowym Rokiem.",
    "Kim był Adam Mickiewicz?",
    "Proszę wymienić polskich architektów i ich dzieła.",
    "Jakie są główne gałęzie przemysłu w Polsce?",
    "Proszę opowiedzieć o polskich zwyczajach związanych z weselem.",
    "Jakie są najważniejsze osiągnięcia polskiej nauki?",
    "Proszę opowiedzieć o polskiej tradycji związanej z Dniem Wszystkich Świętych.",
    "Jakie są najważniejsze muzea w Polsce?",
    "Proszę opowiedzieć o polskich festiwalach filmowych.",
    "Jakie są najważniejsze wydarzenia sportowe w Polsce?",
    "Proszę wymienić polskich polityków i ich rolę w historii Polski.",
    "Jakie są główne rodzaje transportu w Polsce?",
    "Proszę opowiedzieć o polskich tradycjach związanych z obchodzeniem Dnia Niepodległości.",
    "Jakie są główne problemy środowiskowe w Polsce?",
    "Proszę wymienić polskie czasopisma i gazety.",
    "Jakie są najważniejsze osiągnięcia polskiej literatury?",
    "Proszę opowiedzieć o polskich wynalazkach i ich wynalazcach.",
    "Jakie są najważniejsze zabytki we Wrocławiu?",
    "Proszę opowiedzieć o polskich sportach narodowych.",
    "Jakie są główne cele polskiej polityki zagranicznej?",
    "Proszę wymienić polskie seriale telewizyjne i ich popularność.",
    "Jakie są najważniejsze atrakcje turystyczne w regionie Mazur?",
    "Proszę opowiedzieć o polskich tradycjach związanych z chrztem.",
    "Jakie są główne cele polskiej polityki gospodarczej?",
    "Proszę wymienić polskich artystów teatralnych i ich osiągnięcia.",
    "Jakie są najważniejsze wydarzenia z historii Polski w XIX wieku?",
    "Proszę opowiedzieć o polskich tradycjach związanych z obchodzeniem Święta Zmarłych."
]

# TMDB API Configuration
TMDB_API_URL = "https://api.themoviedb.org/3/discover/movie"
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# List of emojis to use for the header
EMOJIS = ["🎬", "🍿", "🎥", "📽️", "🎞️", "📺", "🎭"]

# Time settings for schedulers
PHRASES_SCHEDULE = {
    "day_of_week": "mon,fri",
    "hour": 1,
    "minute": 19
}

FACTS_SCHEDULE = {
    "day_of_week": "thu",
    "hour": 22,
    "minute": 9
}

MOVIES_SCHEDULE = {
    "day_of_week": "sat",
    "hour": 17,
    "minute": 30
}
