from services.db import mongo

async def is_new_user(user_id: int):
    user = await mongo.users.find_one({"user_id": user_id})
    return user is None

async def add_new_user(user_id: int, username: str):
    await mongo.users.insert_one({"user_id": user_id, "username": username})
