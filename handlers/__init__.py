from aiogram import Dispatcher
from .start import register_start_handlers
from .test import register_test_handlers
from .interview import register_interview_handlers

async def register_handlers(dp: Dispatcher):
    register_start_handlers(dp)
    await register_test_handlers(dp)
    register_interview_handlers(dp)