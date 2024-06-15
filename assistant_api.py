import aiohttp
import json

class AssistantsAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def call_assistant(self, model, messages, max_tokens, temperature):
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                return await response.json()

    async def create_assistant(self, model, name=None, description=None, instructions=None, tools=None, tool_resources=None, metadata=None, temperature=1, top_p=1, response_format=None):
        url = f"{self.base_url}/assistants"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "OpenAI-Beta": "assistants=v2"
        }
        payload = {
            "model": model,
            "name": name,
            "description": description,
            "instructions": instructions,
            "tools": tools or [],
            "tool_resources": tool_resources,
            "metadata": metadata,
            "temperature": temperature,
            "top_p": top_p,
            "response_format": response_format
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                return await response.json()
