import random
import requests
from aiogram import Bot
from aiogram.types import InputMediaPhoto
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import config

movies_scheduler = AsyncIOScheduler()

# Function to fetch total number of pages from TMDB API
def fetch_total_pages():
    params = {
        "api_key": config.TMDB_API_KEY,
        "language": "pl-PL",  # Fetch data in Polish
        "page": 1,
    }
    response = requests.get(f"{config.TMDB_API_URL}/popular", params=params)
    response.raise_for_status()
    total_pages = response.json().get("total_pages", 1)
    print(f"Total pages available: {total_pages}")
    return total_pages

# Function to fetch movies from a random page in TMDB API
async def fetch_movies():
    total_pages = fetch_total_pages()
    valid_movies = []
    current_date = datetime.now().date()
    
    while len(valid_movies) < 6:
        random_page = random.randint(1, min(total_pages, 500))  # Ensure we don't exceed TMDB limits
        params = {
            "api_key": config.TMDB_API_KEY,
            "language": "pl-PL",  # Fetch data in Polish
            "page": random_page,
        }
        print(f"Fetching movies from page: {random_page}")
        response = requests.get(f"{config.TMDB_API_URL}/popular", params=params)
        response.raise_for_status()
        movies = response.json().get("results", [])
        
        for movie in movies:
            release_date = movie.get('release_date', '')
            if release_date:
                release_date_obj = datetime.strptime(release_date, "%Y-%m-%d").date()
                release_year = release_date_obj.year
                rating = float(movie.get('vote_average', 0))
                if (movie.get('poster_path') and release_year >= 2000 and
                        release_date_obj <= current_date and
                        16 not in movie.get('genre_ids', []) and 
                        movie.get('original_language') != 'zh' and
                        rating >= 8.5 and len(valid_movies) < 6):
                    valid_movies.append(movie)
                    if len(valid_movies) >= 6:
                        break

    return valid_movies

# Function to send movies to Telegram
async def send_movies(bot: Bot):
    try:
        movies = await fetch_movies()  # Fetch movies
        media = []
        header_emoji = random.choice(config.EMOJIS)
        description = f"<b>{header_emoji} Podbórka filmów dla poziomów A1-B2</b>\n\n"
        
        for movie in movies:
            image_url = f"{config.TMDB_IMAGE_BASE_URL}{movie['poster_path']}"
            title = movie['title']  # Ensure the title is in Polish
            year = movie['release_date'][:4]
            rating = int(float(movie['vote_average']))
            media.append(InputMediaPhoto(media=image_url))
            description += f"<b>{title}</b> ({year}) ⭐ {rating}\n"
        
        description += "\nPodziel się wrażeniami z oglądania w komentarzach!👇\n\n@polishdom"

        # Add caption to the first image
        media[0].caption = description
        media[0].parse_mode = 'HTML'

        # Send the media group with the first image having the caption
        await bot.send_media_group(chat_id=config.CHANNEL_ID, media=media)

    except Exception as e:
        print(f"Error sending movies: {e}")

# Scheduler to send movies
schedule_movies = send_movies
