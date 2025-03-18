import aiohttp
import aiofiles
import os

async def transcribe_audio(file_path):
    API_KEY = os.getenv("OPENAI_API_KEY")
    
    async with aiofiles.open(file_path, "rb") as audio_file:
        audio_data = await audio_file.read()
    
    data = aiohttp.FormData()
    data.add_field("file", audio_data, filename="audio.ogg")
    data.add_field("model", "whisper-1")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers=headers,
            data=data
        ) as response:
            result = await response.json()
            return result.get("text", "")