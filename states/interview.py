from aiogram.fsm.state import State, StatesGroup
from datetime import datetime


# Состояния интервью
class InterviewStates(StatesGroup):
    waiting_answer = State()
    completed = State()

    def __init__(self):
        super().__init__()
        self.questions = []
        self.answers = [] 