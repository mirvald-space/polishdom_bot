import logging

from aiogram import types


async def unknown_command(message: types.Message):
    logging.info("Called unknown_command")
    if message.text and message.text.startswith('/'):
        await message.answer("Извините, я не понимаю эту команду. Пожалуйста, используйте /start или /status.")
