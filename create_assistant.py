import asyncio
import json
from assistant_api import AssistantsAPI
import config

async def create_new_assistant():
    assistants_api = AssistantsAPI(api_key=config.ASSISTANTS_API_KEY)
    response = await assistants_api.create_assistant(
        model="gpt-4-turbo",
        name="Polish Language Assistant",
        description="An assistant to help with learning the Polish language.",
        instructions="You are an expert in the Polish language. Generate 10 brief conversational phrases in Polish.",
        tools=[{"type": "code_interpreter"}],  # Updated to object
        metadata={"project": "polishdom_bot"},
        temperature=0.7,
        top_p=1
    )
    with open("assistant_config.json", "w") as file:
        json.dump(response, file, indent=2)
    print("Assistant created and configuration saved.")

asyncio.run(create_new_assistant())
