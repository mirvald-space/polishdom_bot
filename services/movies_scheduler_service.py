import random
import requests
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import config

movies_scheduler = AsyncIOScheduler()

# Function to fetch total number of pages from TMDB API
def fetch_total_pages():
    params = {
        "api_key": config.TMDB_API_KEY,
        "language": "pl-PL",
        "sort_by": "popularity.desc",
        "vote_average.gte": 6,
        "page": 1,
    }
    response = requests.get(config.TMDB_API_URL, params=params)
    response.raise_for_status()
    total_pages = response.json().get("total_pages", 1)
    print(f"Total pages available: {total_pages}")
    return total_pages

# Function to fetch movies from a random page in TMDB API
async def fetch_movies():
    total_pages = fetch_total_pages()
    random_page = random.randint(1, min(total_pages, 500))  # Ensure we don't exceed TMDB limits
    params = {
        "api_key": config.TMDB_API_KEY,
        "language": "pl-PL",
        "sort_by": "popularity.desc",
        "vote_average.gte": 6,
        "page": random_page,
    }
    print(f"Fetching movies from page: {random_page}")
    response = requests.get(config.TMDB_API_URL, params=params)
    response.raise_for_status()
    movies = response.json().get("results", [])
    return random.sample(movies, 6)  # Select 6 random movies

# Function to send movies to Telegram
async def send_movies(bot: Bot):
    try:
        movies = await fetch_movies()  # Fetch movies
        media = []
        header_emoji = random.choice(config.EMOJIS)
        description = f"<b>{header_emoji} Подборка фильмов для уровней A1-B2</b>\n\n"
        
        for movie in movies:
            image_url = f"{config.TMDB_IMAGE_BASE_URL}{movie['poster_path']}"
            title = movie['title']
            year = movie['release_date'][:4]
            rating = int(float(movie['vote_average']))
            media.append(InputMediaPhoto(media=image_url))
            description += f"<b>{title}</b> ({year}) ⭐ {rating}\n"
        
        description += "\nДелитесь впечатлениями о просмотре в комментариях!👇\n\n@polishdom"

        # Add caption to the first image
        media[0].caption = description
        media[0].parse_mode = 'HTML'

        # Send the media group with the first image having the caption
        await bot.send_media_group(chat_id=config.CHANNEL_ID, media=media)

    except Exception as e:
        print(f"Error sending movies: {e}")

# Scheduler to send movies
schedule_movies = send_movies
